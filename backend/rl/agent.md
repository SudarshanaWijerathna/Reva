# -*- coding: utf-8 -*-
"""
================================================================================
Project Reva — Reinforcement Learning Environment for Real Estate Portfolio
================================================================================
University of Moratuwa

Description:
    This module implements a Deep Q-Network (DQN) based RL agent for real estate
    portfolio management. The agent learns WHEN to buy, sell, or hold properties
    by consuming outputs from four upstream supervised ML models:

        1. Sentiment Analyzer      → daily sentiment scores  (HIGH-FREQUENCY)
        2. Land Price Predictor    → predicted land price trend       (monthly)
        3. Rental Price Predictor  → predicted rental yield trend     (monthly)
        4. Housing Price Predictor → predicted housing price change   (monthly)

    The RL agent does NOT predict prices. It uses those predictions as signals
    in its state vector and learns the optimal action policy through trial and
    error across simulated market episodes.

── WHY SENTIMENT IS TREATED DIFFERENTLY ────────────────────────────────────────
    Real estate transactions happen monthly, but the signals that drive them —
    news, political events, global shocks — can shift within hours.

    Example events that move market sentiment overnight:
        - Central Bank of Sri Lanka interest rate decision
        - Election result or government policy announcement
        - Global recession fears / IMF news
        - A major infrastructure project approval in a district

    If we only feed the agent a single monthly average sentiment score, it is
    blind to:
        - The DIRECTION sentiment has been moving (improving vs worsening)
        - The STABILITY of sentiment (calm market vs political crisis)
        - SUDDEN SHOCKS (e.g., a ±2σ spike from an unexpected event)

    Solution: The SentimentAggregator runs at DAILY frequency and produces
    four features per property per month:

        1. sentiment_current    — most recent 7-day average (present state)
        2. sentiment_trend      — linear slope over 30 days (momentum)
        3. sentiment_volatility — std dev over 30 days (market stability)
        4. sentiment_shock      — binary: did a major shock occur this month?

    These replace the single monthly average in the state vector.
    The RL loop stays monthly — only the richness of the sentiment signal changes.

── ARCHITECTURE ─────────────────────────────────────────────────────────────────

    High-frequency (daily):
        Raw daily sentiment scores
            └──> SentimentAggregator
                    └──> 4 features/property: [current, trend, volatility, shock]

    Low-frequency (monthly):
        Land Price Predictor    └──> land_trend
        Rental Price Predictor  └──> rental_yield
        Housing Price Predictor └──> housing_signal

    Combined:
        └──> MultiPropertyEnv state vector (N*8 + 1)
                └──> DQN Agent → BUY / SELL / HOLD per property

── STATE VECTOR (for property i, repeated N times) ──────────────────────────────

    Index  Feature                Source
    ─────────────────────────────────────────────────────────────
    0      units_owned            environment
    1      sentiment_current      SentimentAggregator (daily→monthly)
    2      sentiment_trend        SentimentAggregator
    3      sentiment_volatility   SentimentAggregator
    4      sentiment_shock        SentimentAggregator
    5      land_trend             Land Price Predictor
    6      rental_yield           Rental Price Predictor
    7      housing_signal         Housing Price Predictor
    ─────────────────────────────────────────────────────────────
    N*8    cash_in_hand           environment (normalised)
    ─────────────────────────────────────────────────────────────

    Total state dimension = N * 8 + 1

Key Design Decisions:
    - RL timestep stays MONTHLY — real estate transactions don't happen daily
    - Only sentiment is daily; all other signals remain monthly
    - SentimentAggregator bridges the daily→monthly gap without changing the RL loop
    - Transaction costs (2%) model real-world friction and discourage over-trading
    - Reward = portfolio value change + rental income earned this month

Usage:
    See the __main__ block at the bottom for a complete training/testing example.

Dependencies:
    tensorflow >= 2.x, numpy, pandas, scikit-learn, tqdm
================================================================================
"""

import numpy as np
import pandas as pd
import itertools
import os
import pickle
from datetime import datetime

import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input, BatchNormalization
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

tf.random.set_seed(42)
np.random.seed(42)


# ==============================================================================
# SECTION 1: REPLAY BUFFER
# ==============================================================================

class ReplayBuffer:
    """
    Circular experience replay memory for the DQN agent.

    ── Why Experience Replay? ───────────────────────────────────────────────────
    Without replay, the agent trains on each transition the moment it occurs.
    Problem: consecutive transitions share the same market trend (month 3 →
    month 4 → month 5 are all correlated), causing the Q-network to overfit
    recent patterns and forget earlier ones — unstable training.

    The fix:
        1. Store every transition (s, a, r, s', done) in a large buffer
        2. Train on RANDOMLY SAMPLED mini-batches from this buffer
        3. Random sampling breaks temporal correlations → stable gradients

    Think of it as: instead of reacting to the last trade immediately, write it
    in a journal, then later study a random selection of all past trades.

    ── Circular Buffer ──────────────────────────────────────────────────────────
    When full, new transitions overwrite the oldest (FIFO). This bounds memory
    while keeping the buffer populated with recent experience.

    Attributes:
        obs1_buf (np.ndarray): States before action,  shape [size, obs_dim]
        obs2_buf (np.ndarray): States after action,   shape [size, obs_dim]
        acts_buf (np.ndarray): Actions taken,         shape [size]
        rews_buf (np.ndarray): Rewards received,      shape [size]
        done_buf (np.ndarray): Episode-end flags,     shape [size]
        ptr      (int): Current write position
        size     (int): Number of valid transitions stored
        max_size (int): Maximum buffer capacity
    """

    def __init__(self, obs_dim: int, act_dim: int, size: int = 10000):
        """
        Initialise replay buffer with pre-allocated NumPy arrays.

        Pre-allocation avoids dynamic resizing overhead and allows O(1)
        random-index access during batch sampling.

        Args:
            obs_dim (int): State vector dimensionality. For N properties: N*8+1.
            act_dim (int): Number of actions (kept for API consistency).
            size    (int): Buffer capacity. Default 10000.
        """
        self.obs1_buf = np.zeros([size, obs_dim], dtype=np.float32)
        self.obs2_buf = np.zeros([size, obs_dim], dtype=np.float32)
        self.acts_buf = np.zeros(size, dtype=np.uint8)
        self.rews_buf = np.zeros(size, dtype=np.float32)
        self.done_buf = np.zeros(size, dtype=np.uint8)
        self.ptr, self.size, self.max_size = 0, 0, size

    def store(self, obs: np.ndarray, act: int, rew: float,
              next_obs: np.ndarray, done: bool):
        """
        Store one transition. Overwrites oldest entry when buffer is full.

        Args:
            obs      (np.ndarray): Scaled state BEFORE the action.
            act      (int):        Action index taken.
            rew      (float):      Reward received.
            next_obs (np.ndarray): Scaled state AFTER the action.
            done     (bool):       True if this step ended the episode.
        """
        self.obs1_buf[self.ptr] = obs
        self.obs2_buf[self.ptr] = next_obs
        self.acts_buf[self.ptr] = act
        self.rews_buf[self.ptr] = rew
        self.done_buf[self.ptr] = done
        self.ptr  = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample_batch(self, batch_size: int = 32) -> dict:
        """
        Randomly sample a mini-batch of transitions for Q-network training.

        Args:
            batch_size (int): Number of transitions to sample. Default 32.

        Returns:
            dict: keys 's', 's2', 'a', 'r', 'd' — shapes (batch_size, ...).
        """
        idxs = np.random.randint(0, self.size, size=batch_size)
        return dict(
            s=self.obs1_buf[idxs],
            s2=self.obs2_buf[idxs],
            a=self.acts_buf[idxs],
            r=self.rews_buf[idxs],
            d=self.done_buf[idxs]
        )


# ==============================================================================
# SECTION 2: SENTIMENT AGGREGATOR
# ==============================================================================

class SentimentAggregator:
    """
    Converts a stream of daily sentiment scores into monthly RL state features.

    ── The Problem ──────────────────────────────────────────────────────────────
    A single monthly average sentiment score loses all within-month dynamics.
    Two months with the same average can be completely different situations:

        Month A: stable +0.6 throughout         → calm, confidently bullish
        Month B: started +0.8, crashed to -0.4  → momentum is negative, risky

    The RL agent cannot distinguish these from a single average score.

    ── The Solution: Four Features ──────────────────────────────────────────────
    From the past `window` days of daily sentiment scores, we compute:

        1. current (float, [-1,+1]):
           Mean of the most recent `short_window` (7) days.
           Captures WHERE sentiment is RIGHT NOW.
           A short mean rather than single day reduces single-event noise.

        2. trend (float, unbounded):
           Slope of a linear fit over the full `window` (30) days.
           Positive = sentiment improving (bullish momentum).
           Negative = sentiment deteriorating (bearish momentum).
           This is the most useful feature for detecting political shifts.

        3. volatility (float, ≥0):
           Standard deviation over the full window.
           Low → stable, predictable market.
           High → chaotic, uncertain market (e.g., political crisis week).

        4. shock (float, {0,1}):
           Binary flag. Fires if the recent 7-day mean deviates more than
           `shock_threshold` standard deviations from the monthly mean.
           Designed to catch election results, rate hike announcements, etc.

    ── Integration with the RL Loop ─────────────────────────────────────────────
    The RL agent still steps MONTHLY. At each monthly step, the environment
    calls aggregate_all_properties() to convert the past 30 days of daily data
    into these 4 features, which are embedded in the state vector alongside the
    monthly price signals. The RL loop frequency is unchanged.

    Attributes:
        window          (int):   Lookback days for trend/volatility. Default 30.
        short_window    (int):   Recent days for current score. Default 7.
        shock_threshold (float): Std dev multiplier for shock detection. Default 2.0.
    """

    def __init__(self, window: int = 30, short_window: int = 7,
                 shock_threshold: float = 2.0):
        """
        Initialise the SentimentAggregator.

        Args:
            window          (int):   Lookback window in days. Match to RL timestep
                                     (30 days ≈ 1 month). Default 30.
            short_window    (int):   Recent window for current score. Default 7.
            shock_threshold (float): Std dev multiplier that triggers the shock flag.
                                     2.0 flags events outside ~95% of normal variation.
                                     Default 2.0.
        """
        self.window          = window
        self.short_window    = short_window
        self.shock_threshold = shock_threshold

    def aggregate(self, daily_scores: np.ndarray) -> dict:
        """
        Compute four monthly features from a window of daily sentiment scores.

        Called once per property per month. Uses the past `window` days of
        daily scores from the Sentiment Analyzer model.

        Feature computation in detail:

            current:
                np.mean(daily_scores[-short_window:])
                Average of last 7 days. More robust than a single day.

            trend:
                np.polyfit(x, daily_scores[-window:], deg=1)[0]
                Linear regression slope. Units: sentiment change per day.
                Positive slope = improving. Negative slope = worsening.

            volatility:
                np.std(daily_scores[-window:])
                Standard deviation over the full window.
                High value = unstable/uncertain market conditions.

            shock:
                1.0 if |current - monthly_mean| > shock_threshold * volatility
                0.0 otherwise.
                Fires when recent days are anomalously high or low vs the month.

        Args:
            daily_scores (np.ndarray): Daily sentiment scores for one property.
                Shape: (days,), values in [-1, +1].
                If fewer than `window` days available, uses all available data
                (graceful warm-up handling).

        Returns:
            dict: {
                'current':    float — recent score, approx [-1,+1]
                'trend':      float — daily slope (positive=improving)
                'volatility': float — std dev (≥0)
                'shock':      float — 1.0 if shock detected, else 0.0
            }
        """
        available     = min(len(daily_scores), self.window)
        recent_window = daily_scores[-available:]

        # Feature 1: Current (short-term average)
        short   = min(self.short_window, available)
        current = float(np.mean(recent_window[-short:]))

        # Feature 2: Trend (linear slope over full window)
        if available >= 2:
            x     = np.arange(available)
            trend = float(np.polyfit(x, recent_window, 1)[0])
        else:
            trend = 0.0

        # Feature 3: Volatility (standard deviation)
        volatility = float(np.std(recent_window)) if available >= 2 else 0.0

        # Feature 4: Shock flag (anomalous recent score vs monthly baseline)
        monthly_mean = float(np.mean(recent_window))
        shock        = 0.0
        if volatility > 1e-6:  # avoid division by zero in perfectly flat markets
            deviation = abs(current - monthly_mean) / volatility
            shock     = 1.0 if deviation > self.shock_threshold else 0.0

        return {
            'current':    current,
            'trend':      trend,
            'volatility': volatility,
            'shock':      shock
        }

    def aggregate_all_properties(self, daily_scores_matrix: np.ndarray,
                                  month_end_day: int) -> np.ndarray:
        """
        Aggregate sentiment features for ALL properties at a given month-end.

        Called by MultiPropertyEnv._get_obs() at each monthly step.

        Args:
            daily_scores_matrix (np.ndarray): All daily scores, shape (T_daily, N).
                                              Column i = property i's daily scores.
            month_end_day       (int):        Day index of the current month-end
                                              in the daily array. The aggregator
                                              looks back `window` days from here.

        Returns:
            np.ndarray: Shape (N, 4). Row i = [current, trend, volatility, shock]
                        for property i.
        """
        n_properties = daily_scores_matrix.shape[1]
        features     = np.zeros((n_properties, 4), dtype=np.float32)

        start_day = max(0, month_end_day - self.window)
        end_day   = month_end_day  # exclusive

        for i in range(n_properties):
            daily_slice = daily_scores_matrix[start_day:end_day, i]
            agg         = self.aggregate(daily_slice)
            features[i] = [agg['current'], agg['trend'],
                           agg['volatility'], agg['shock']]

        return features  # (N, 4)


# ==============================================================================
# SECTION 3: NEURAL NETWORK (Q-NETWORK)
# ==============================================================================

def build_q_network(input_dim: int, n_actions: int,
                    n_hidden_layers: int = 2, hidden_dim: int = 64) -> Model:
    """
    Build the Q-Network: MLP mapping states to Q-values.

    ── What is a Q-value? ───────────────────────────────────────────────────────
    Q(s, a) = expected total discounted future reward when in state s,
              taking action a, then following the optimal policy.

    The network learns this function. The agent picks the action with the
    highest Q-value — the one predicted to yield the best long-term outcome.

    ── Architecture ─────────────────────────────────────────────────────────────
        Input  (state vector, size N*8+1)
            → [Dense(hidden_dim, ReLU) + BatchNorm] × n_hidden_layers
            → Dense(n_actions, linear)    ← no activation: Q-values are unbounded

    ── Why BatchNormalization? ───────────────────────────────────────────────────
    The state vector mixes features at very different scales:
        units_owned:         integers [0, ~10]
        sentiment_current:   [-1, +1]
        sentiment_trend:     [-0.05, +0.05]   very small
        sentiment_volatility:[0, 0.5]
        sentiment_shock:     {0, 1}
        land_trend:          [-0.1, +0.15]
        rental_yield:        [0.002, 0.012]   very small
        housing_signal:      [-0.15, +0.20]
        cash_normalised:     [0, ~3]

    BatchNorm re-normalises activations between layers, preventing large-scale
    features from dominating gradients and accelerating convergence.

    Args:
        input_dim       (int): State size. N*8+1 for N properties.
        n_actions       (int): Action count. 3^N.
        n_hidden_layers (int): Number of hidden layers. Default 2.
        hidden_dim      (int): Neurons per hidden layer. Default 64.

    Returns:
        tf.keras.Model: Compiled Keras Q-network.
    """
    i = Input(shape=(input_dim,), name="state_input")
    x = i
    for idx in range(n_hidden_layers):
        x = Dense(hidden_dim, activation='relu', name=f"hidden_{idx+1}")(x)
        x = BatchNormalization(name=f"bn_{idx+1}")(x)
    x = Dense(n_actions, activation='linear', name="q_values")(x)

    model = Model(inputs=i, outputs=x, name="Reva_Q_Network")
    model.compile(loss='mse', optimizer=Adam(learning_rate=1e-3))
    print(model.summary())
    return model


# ==============================================================================
# SECTION 4: THE REAL ESTATE ENVIRONMENT
# ==============================================================================

class MultiPropertyEnv:
    """
    Simulated real estate market environment for RL training (Project Reva).

    Models a portfolio of N properties over monthly timesteps. At each step the
    agent observes the market state — including aggregated sentiment features
    that capture intra-month dynamics — and decides to BUY, SELL, or HOLD each
    property independently.

    ── State Vector Layout (N*8 + 1 total) ──────────────────────────────────────
    For each property i:
        [units_owned, sentiment_current, sentiment_trend, sentiment_volatility,
         sentiment_shock, land_trend, rental_yield, housing_signal]
    Then:
        [cash_in_hand (normalised)]

    ── Action Space ─────────────────────────────────────────────────────────────
    For each property: 0=SELL, 1=HOLD, 2=BUY. Total = 3^N actions.
    Actions are independent per property (e.g., sell p0, buy p1, hold p2).

    ── Reward ───────────────────────────────────────────────────────────────────
    reward = (portfolio_value_after_trade - portfolio_value_before_trade)
           + rental_income_earned_this_month
    Captures both capital appreciation and passive income.

    ── Data Format ──────────────────────────────────────────────────────────────
    monthly_data   : dict of (T_monthly, N) arrays for monthly price signals
    daily_sentiment: (T_daily, N) array — T_daily = T_monthly * days_per_month
    property_prices: (T_monthly, N) array of actual/predicted prices

    Attributes:
        n_step         (int): Monthly timesteps
        n_property     (int): Number of properties
        state_dim      (int): N*8+1
        action_space   (np.ndarray): [0 … 3^N-1]
        action_list    (list): Maps action index → per-property [0/1/2] vector
        sentiment_agg  (SentimentAggregator): Aggregates daily → monthly features
    """

    MONTHLY_SIGNAL_KEYS   = ['land_trend', 'rental_yield', 'housing_signal']
    SENTIMENT_FEATURES    = ['current', 'trend', 'volatility', 'shock']
    # 1 (units) + 4 (sentiment) + 3 (monthly signals) = 8 features per property
    FEATURES_PER_PROPERTY = 8

    def __init__(self,
                 monthly_data:          dict,
                 daily_sentiment:       np.ndarray,
                 property_prices:       np.ndarray,
                 initial_investment:    float = 10_000_000,
                 rental_income_rate:    float = 0.005,
                 transaction_cost_rate: float = 0.02,
                 days_per_month:        int   = 30):
        """
        Initialise the real estate environment.

        Args:
            monthly_data (dict):
                Monthly market signals. Keys: 'land_trend', 'rental_yield',
                'housing_signal'. Each value: np.ndarray shape (T_monthly, N).

                In production, replace with:
                    monthly_data = {
                        'land_trend':     land_model.predict(features),
                        'rental_yield':   rental_model.predict(features),
                        'housing_signal': housing_model.predict(features),
                    }

            daily_sentiment (np.ndarray):
                Daily raw sentiment scores, shape (T_daily, N).
                T_daily = T_monthly * days_per_month.
                Values in [-1, +1] — output of your Sentiment Analyzer.

                In production, replace with:
                    daily_sentiment = sentiment_model.predict(news_feed_daily)

            property_prices (np.ndarray):
                Monthly property prices, shape (T_monthly, N). Units: LKR.
                Used for executing buy/sell transactions each month.

            initial_investment (float):
                Starting capital in LKR. Default 10,000,000 (10M LKR).

            rental_income_rate (float):
                Monthly rental income as fraction of price per unit owned.
                Default 0.005 (0.5%/month ≈ 6% annual yield).

            transaction_cost_rate (float):
                Fraction of transaction value charged as costs (stamp duty,
                agent fees, legal). Default 0.02 (2%).
                Acts as a friction penalty discouraging excessive trading.

            days_per_month (int):
                Daily sentiment datapoints per monthly RL step. Default 30.
        """
        # Validate
        for key in self.MONTHLY_SIGNAL_KEYS:
            assert key in monthly_data, f"Missing key: '{key}'"

        T_monthly, N = monthly_data['land_trend'].shape
        assert daily_sentiment.shape == (T_monthly * days_per_month, N), (
            f"daily_sentiment shape {daily_sentiment.shape} expected "
            f"({T_monthly * days_per_month}, {N})"
        )
        assert property_prices.shape == (T_monthly, N)

        self.n_step      = T_monthly
        self.n_property  = N

        # Data arrays
        self.land_trend      = monthly_data['land_trend'].astype(np.float32)
        self.rental_yield    = monthly_data['rental_yield'].astype(np.float32)
        self.housing_signal  = monthly_data['housing_signal'].astype(np.float32)
        self.daily_sentiment = daily_sentiment.astype(np.float32)
        self.property_prices = property_prices.astype(np.float32)

        # Sentiment aggregator (bridges daily → monthly)
        self.sentiment_agg  = SentimentAggregator(
            window=days_per_month, short_window=7, shock_threshold=2.0
        )
        self.days_per_month = days_per_month

        # Environment parameters
        self.initial_investment    = initial_investment
        self.rental_income_rate    = rental_income_rate
        self.transaction_cost_rate = transaction_cost_rate

        # Action space: 3^N actions
        self.action_space = np.arange(3 ** self.n_property)
        self.action_list  = list(
            map(list, itertools.product([0, 1, 2], repeat=self.n_property))
        )

        # State dimension: N*8 + 1
        self.state_dim = self.n_property * self.FEATURES_PER_PROPERTY + 1

        # Mutable state (reset each episode)
        self.cur_step     = None
        self.units_owned  = None
        self.cur_prices   = None
        self.cash_in_hand = None

        self.reset()

    def reset(self) -> np.ndarray:
        """
        Reset to the start of a new episode.

        Clears owned units, restores cash to initial_investment,
        and returns the initial state observation.

        Returns:
            np.ndarray: Initial state vector, shape (state_dim,).
        """
        self.cur_step     = 0
        self.units_owned  = np.zeros(self.n_property, dtype=np.float32)
        self.cur_prices   = self.property_prices[0]
        self.cash_in_hand = float(self.initial_investment)
        return self._get_obs()

    def step(self, action: int) -> tuple:
        """
        Execute one monthly timestep.

        Sequence:
            1. Record portfolio value before the action
            2. Execute trade (sell/hold/buy per property)
            3. Collect rental income from owned units
            4. Advance to next month
            5. Compute reward = value change + rental income
            6. Return (next_state, reward, done, info)

        Args:
            action (int): Action index [0, 3^N - 1].

        Returns:
            tuple: (next_state, reward, done, info)
                next_state (np.ndarray): New state, shape (state_dim,).
                reward     (float):      Portfolio change + rental income (LKR).
                done       (bool):       True if time series exhausted.
                info       (dict):       cur_val, rental_income, cash, units_owned.
        """
        assert action in self.action_space

        prev_val = self._get_portfolio_value()
        self._trade(action)

        # Rental income: units_owned[i] * price[i] * monthly_rate
        rental_income = float(
            np.sum(self.units_owned * self.cur_prices * self.rental_income_rate)
        )
        self.cash_in_hand += rental_income

        # Advance month
        self.cur_step  += 1
        if self.cur_step < self.n_step: # Check if not at the end of the data
            self.cur_prices = self.property_prices[self.cur_step]
        else:
            # If it's the last step, cur_prices should remain as the last valid price
            pass

        cur_val = self._get_portfolio_value()
        reward  = (cur_val - prev_val) + rental_income
        done    = self.cur_step == self.n_step - 1

        info = {
            'cur_val':       cur_val,
            'rental_income': rental_income,
            'cash':          self.cash_in_hand,
            'units_owned':   self.units_owned.copy()
        }
        return self._get_obs(), reward, done, info

    def _get_obs(self) -> np.ndarray:
        """
        Construct the state vector for the current timestep.

        Layout (8 features per property, then cash):
            [units, sent_current, sent_trend, sent_vol, sent_shock,
             land_trend, rental_yield, housing_signal,   ← property 0
             ... repeated for properties 1..N-1 ...,
             cash_normalised]

        Sentiment features are computed by SentimentAggregator using all
        daily data up to the end of the current month.

        Returns:
            np.ndarray: Shape (state_dim,) = (N*8+1,).
        """
        obs = np.zeros(self.state_dim, dtype=np.float32)
        t   = self.cur_step

        # Compute aggregated sentiment features for all properties this month
        # month_end_day = end-exclusive day index for month t
        month_end_day      = (t + 1) * self.days_per_month
        sentiment_features = self.sentiment_agg.aggregate_all_properties(
            self.daily_sentiment, month_end_day
        )
        # sentiment_features: (N, 4) = [current, trend, volatility, shock]

        for i in range(self.n_property):
            base = i * self.FEATURES_PER_PROPERTY
            obs[base + 0] = self.units_owned[i]           # units held
            obs[base + 1] = sentiment_features[i, 0]      # sentiment: current
            obs[base + 2] = sentiment_features[i, 1]      # sentiment: trend
            obs[base + 3] = sentiment_features[i, 2]      # sentiment: volatility
            obs[base + 4] = sentiment_features[i, 3]      # sentiment: shock
            obs[base + 5] = self.land_trend[t, i]         # land price trend
            obs[base + 6] = self.rental_yield[t, i]       # rental yield
            obs[base + 7] = self.housing_signal[t, i]     # housing price signal

        # Normalised cash: prevents cash from dominating the state scale
        obs[-1] = self.cash_in_hand / self.initial_investment
        return obs

    def _get_portfolio_value(self) -> float:
        """
        Compute total portfolio value = (units · prices) + cash.

        Returns:
            float: Total portfolio value in LKR.
        """
        return float(self.units_owned.dot(self.cur_prices) + self.cash_in_hand)

    def _trade(self, action: int):
        """
        Execute buy/sell/hold per property for one timestep.

        Decodes action index → per-property vector via action_list:
            0 = SELL: sell ALL units; net proceeds (after cost) go to cash
            1 = HOLD: do nothing
            2 = BUY:  buy ONE unit if cash covers cost + transaction fee

        Sells execute BEFORE buys so selling one property can fund buying another.

        Transaction cost rationale:
            - Stamp duty (Sri Lanka):   ~3–4% of transaction value
            - Agent + legal fees:        ~1–2%
            - Default combined:          2% (conservative lower bound)
        This friction penalises excessive trading and mirrors real-world costs.

        Args:
            action (int): Action index decoded via self.action_list.
        """
        action_vec   = self.action_list[action]
        sell_indices = [i for i, a in enumerate(action_vec) if a == 0]
        buy_indices  = [i for i, a in enumerate(action_vec) if a == 2]

        # Sell first (free up cash before buying)
        for i in sell_indices:
            if self.units_owned[i] > 0:
                gross               = self.cur_prices[i] * self.units_owned[i]
                net                 = gross * (1 - self.transaction_cost_rate)
                self.cash_in_hand  += net
                self.units_owned[i] = 0

        # Buy one unit per targeted property if affordable
        for i in buy_indices:
            total_cost = self.cur_prices[i] * (1 + self.transaction_cost_rate)
            if self.cash_in_hand >= total_cost:
                self.units_owned[i] += 1
                self.cash_in_hand   -= total_cost
            # If unaffordable: silently treat as HOLD


# ==============================================================================
# SECTION 5: UTILITY FUNCTIONS
# ==============================================================================

def get_scaler(env: MultiPropertyEnv) -> StandardScaler:
    """
    Fit a StandardScaler by running one random-action episode.

    ── Why Normalise? ───────────────────────────────────────────────────────────
    The state vector mixes features at very different magnitudes. Without
    normalisation, Q-network gradients are dominated by the largest-scale
    features (e.g., cash), making training slow and unstable.

    StandardScaler transforms each feature to mean=0, std=1.

    ── Process ──────────────────────────────────────────────────────────────────
    1. Run one full episode with uniformly random actions
    2. Collect all state vectors encountered
    3. Fit StandardScaler on this collection
    4. Reset environment and return the fitted scaler

    The random episode covers the full time series, giving a representative
    sample of state distributions for the scaler to fit on.

    Args:
        env (MultiPropertyEnv): Initialised environment.

    Returns:
        StandardScaler: Fitted scaler. Use scaler.transform([state]) before
                        feeding states to the Q-network.
    """
    states = []
    state  = env.reset()
    done   = False

    while not done:
        action = np.random.choice(env.action_space)
        next_state, _, done, _ = env.step(action)
        states.append(state)
        state = next_state

    scaler = StandardScaler()
    scaler.fit(states)
    env.reset()
    return scaler


def maybe_make_dir(directory: str):
    """Create a directory if it does not already exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"  Created directory: {directory}")


def generate_synthetic_data(n_properties:   int   = 3,
                             n_months:       int   = 120,
                             days_per_month: int   = 30,
                             base_price:     float = 5_000_000,
                             seed:           int   = 42) -> tuple:
    """
    Generate synthetic market data for development and RL training.

    ── Purpose ──────────────────────────────────────────────────────────────────
    In production this is replaced by real model outputs:
        daily_sentiment              = sentiment_model.predict(news_daily)
        monthly_data['land_trend']   = land_model.predict(location_features)
        monthly_data['rental_yield'] = rental_model.predict(property_features)
        monthly_data['housing_signal']= housing_model.predict(comp_sales)

    This function lets you train the RL agent before those models are ready.

    ── Synthetic Signal Design ───────────────────────────────────────────────────
    property_prices:
        Monthly random walk, upward drift (0.4%/month mean, 2% std).

    daily_sentiment:
        Correlated with monthly price trend (lagged + noise) + occasional
        shock events (sudden ±0.6 spikes for 3–10 days) to exercise the
        SentimentAggregator shock detection feature.
        Shape: (n_months * days_per_month, n_properties).

    land_trend:
        Month-over-month price change, clipped to [-10%, +15%].

    rental_yield:
        Stable ~0.5–0.7%/month (6–8.4% annual), small noise.

    housing_signal:
        3-month forward price change + noise (mimics predictor output).

    Args:
        n_properties   (int):   Number of properties. Default 3.
        n_months       (int):   Monthly timesteps. Default 120 (10 years).
        days_per_month (int):   Daily points per month. Default 30.
        base_price     (float): Starting price per property (LKR). Default 5M.
        seed           (int):   Random seed. Default 42.

    Returns:
        tuple: (monthly_data, daily_sentiment, property_prices)
            monthly_data    (dict):       {land_trend, rental_yield, housing_signal}
            daily_sentiment (np.ndarray): shape (n_months*30, n_properties)
            property_prices (np.ndarray): shape (n_months, n_properties)
    """
    rng    = np.random.RandomState(seed)
    n_days = n_months * days_per_month

    '''# Monthly property prices: random walk with upward drift
    prices    = np.zeros((n_months, n_properties), dtype=np.float32)
    prices[0] = base_price * (1 + rng.uniform(-0.3, 0.3, n_properties))
    for t in range(1, n_months):
        prices[t] = prices[t-1] * (1 + rng.normal(0.004, 0.02, n_properties))
'''
    prices = prices_loaded
    # Monthly signals
    land_trend        = np.zeros_like(prices)
    land_trend[1:]    = (prices[1:] - prices[:-1]) / prices[:-1]
    land_trend        = np.clip(land_trend, -0.10, 0.15)

    housing_signal        = np.zeros_like(prices)
    housing_signal[:-3]   = (prices[3:] - prices[:-3]) / prices[:-3]
    housing_signal       += rng.normal(0, 0.01, prices.shape)
    housing_signal        = np.clip(housing_signal, -0.15, 0.20)

    rental_yield = np.clip(
        0.006 + rng.normal(0, 0.001, prices.shape), 0.002, 0.012
    ).astype(np.float32)

    monthly_data = {
        'land_trend':     land_trend.astype(np.float32),
        'rental_yield':   rental_yield,
        'housing_signal': housing_signal.astype(np.float32)
    }

    # Daily sentiment: correlated with price trend + injected shocks
    daily_base      = np.repeat(land_trend, days_per_month, axis=0)
    daily_sentiment = np.tanh(
        daily_base * 10 + rng.normal(0, 0.15, (n_days, n_properties))
    )

    # Inject shock events (~2 per year per property)
    n_shocks = int(n_months / 6 * n_properties)
    for _ in range(n_shocks):
        day   = rng.randint(0, n_days)
        prop  = rng.randint(0, n_properties)
        mag   = rng.choice([-0.6, +0.6])    # sudden large shift
        dur   = rng.randint(3, 10)           # lasts 3–10 days
        daily_sentiment[day:min(day+dur, n_days), prop] += mag

    daily_sentiment = np.clip(daily_sentiment, -1.0, 1.0).astype(np.float32)

    return monthly_data, daily_sentiment, prices.astype(np.float32)


# ==============================================================================
# SECTION 6: DQN AGENT
# ==============================================================================

class DQNAgent:
    """
    Deep Q-Network Agent for Project Reva.

    Learns a portfolio management policy via the DQN algorithm (Mnih et al., 2015).
    Maps monthly market states (including aggregated sentiment dynamics) to
    buy/sell/hold decisions across all properties.

    ── DQN Algorithm Summary ────────────────────────────────────────────────────
    1.  Observe state s
    2.  Choose action a via ε-greedy:
            with prob ε   → random action (explore)
            with prob 1-ε → argmax Q(s, a) (exploit)
    3.  Execute action → receive reward r, observe next state s'
    4.  Store (s, a, r, s', done) in replay buffer
    5.  Sample random mini-batch from buffer
    6.  Compute Bellman targets:
            target = r + γ * max Q(s', a')   [if not terminal]
            target = r                        [if terminal]
    7.  Train network to minimise MSE(Q(s,a), target)
    8.  Decay ε
    9.  Repeat

    ── Discount Factor γ = 0.95 (monthly steps) ─────────────────────────────────
        Reward 6 months out:  0.95^6  ≈ 0.74  (still matters a lot)
        Reward 12 months out: 0.95^12 ≈ 0.54  (moderate weight)
        Reward 24 months out: 0.95^24 ≈ 0.29  (low but non-zero)
    Encourages ~1–2 year planning horizon, appropriate for real estate.

    Attributes:
        state_size    (int):        N*8+1
        action_size   (int):        3^N
        memory        (ReplayBuffer)
        gamma         (float):      0.95
        epsilon       (float):      current exploration rate
        epsilon_min   (float):      0.01
        epsilon_decay (float):      0.995
        model         (tf.keras.Model): Q-network
    """

    def __init__(self, state_size: int, action_size: int,
                 buffer_size: int = 10000):
        """
        Initialise DQN agent.

        Args:
            state_size  (int): State vector size.
            action_size (int): Number of discrete actions.
            buffer_size (int): Replay buffer capacity. Default 10000.
        """
        self.state_size   = state_size
        self.action_size  = action_size
        self.memory       = ReplayBuffer(state_size, action_size, size=buffer_size)

        self.gamma         = 0.95
        self.epsilon       = 1.0
        self.epsilon_min   = 0.01
        self.epsilon_decay = 0.995

        self.model = build_q_network(state_size, action_size,
                                     n_hidden_layers=2, hidden_dim=64)

    def update_replay_memory(self, state: np.ndarray, action: int,
                              reward: float, next_state: np.ndarray, done: bool):
        """
        Store a transition in the replay buffer.

        Called after every environment step during training.

        Args:
            state      (np.ndarray): Scaled current state, shape (1, state_size).
            action     (int):        Action index taken.
            reward     (float):      Reward received.
            next_state (np.ndarray): Scaled next state, shape (1, state_size).
            done       (bool):       True if episode ended.
        """
        self.memory.store(state[0], action, reward, next_state[0], done)

    def act(self, state: np.ndarray) -> int:
        """
        Select action via epsilon-greedy policy.

        ε-greedy logic:
            With probability ε:     random action (exploration)
            With probability 1-ε:   argmax Q(s,a) (exploitation)

        ε starts at 1.0 and decays toward 0.01 over training.

        Args:
            state (np.ndarray): Scaled state, shape (1, state_size).

        Returns:
            int: Action index.
        """
        if np.random.rand() <= self.epsilon:
            return int(np.random.choice(self.action_size))
        q_values = self.model.predict(state, verbose=0)
        return int(np.argmax(q_values[0]))

    def replay(self, batch_size: int = 32):
        """
        Sample a mini-batch and perform one Q-network gradient update.

        ── Bellman Update ───────────────────────────────────────────────────────
        For each sampled (s, a, r, s', done):
            target = r + (1-done) * γ * max_a'[ Q(s', a') ]

        The (1-done) term zeros out the future term for terminal transitions.

        ── Selective Q-update ───────────────────────────────────────────────────
        We only update Q(s, a_taken):
            1. Predict target_full = Q(s, all_actions)
            2. Overwrite target_full[i, a_i] = computed_target
            3. Train on (states, target_full)
        Gradients only propagate through the Q-value for the taken action.

        Args:
            batch_size (int): Mini-batch size. Default 32.
        """
        if self.memory.size < batch_size:
            return

        batch       = self.memory.sample_batch(batch_size)
        states      = batch['s']
        actions     = batch['a']
        rewards     = batch['r']
        next_states = batch['s2']
        dones       = batch['d']

        next_q     = self.model.predict(next_states, verbose=0)
        max_next_q = np.amax(next_q, axis=1)
        target     = rewards + (1 - dones) * self.gamma * max_next_q

        target_full = self.model.predict(states, verbose=0)
        target_full[np.arange(batch_size), actions] = target

        self.model.train_on_batch(states, target_full)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, filepath: str):
        """Load model weights from disk."""
        self.model.load_weights(filepath)
        print(f"  Loaded weights: {filepath}")

    def save(self, filepath: str):
        """Save model weights to disk."""
        self.model.save_weights(filepath)
        print(f"  Saved weights:  {filepath}")


# ==============================================================================
# SECTION 7: EPISODE RUNNER
# ==============================================================================

def play_one_episode(agent:      DQNAgent,
                     env:        MultiPropertyEnv,
                     scaler:     StandardScaler,
                     is_train:   bool,
                     batch_size: int = 32) -> dict:
    """
    Run one complete episode from month 0 to the last month.

    TRAIN mode:
        - Agent uses ε-greedy action selection (explores)
        - Every step: store in buffer → call replay() → learn
        - ε decays over steps → gradually more exploitation

    TEST mode:
        - Agent acts greedily (ε ≈ 0): always picks best known action
        - No buffer updates, no replay() calls
        - Evaluates the learned policy on unseen data

    Args:
        agent      (DQNAgent):          RL agent.
        env        (MultiPropertyEnv):  Real estate environment.
        scaler     (StandardScaler):    Fitted state normaliser.
        is_train   (bool):              True → train; False → evaluate.
        batch_size (int):               Replay batch size. Default 32.

    Returns:
        dict:
            'final_value'  (float):      Portfolio value at episode end (LKR).
            'total_reward' (float):      Sum of all rewards across the episode.
            'n_trades'     (int):        Number of non-HOLD actions taken.
            'final_units'  (np.ndarray): Units owned per property at end.
    """
    state = env.reset()
    state = scaler.transform([state])   # (1, state_dim)
    done  = False
    total_reward = 0.0
    n_trades     = 0

    while not done:
        action                     = agent.act(state)
        next_state, reward, done, info = env.step(action)
        next_state                 = scaler.transform([next_state])

        n_trades += sum(1 for a in env.action_list[action] if a != 1)

        if is_train:
            agent.update_replay_memory(state, action, reward, next_state, done)
            agent.replay(batch_size)

        state         = next_state
        total_reward += reward

    return {
        'final_value':  info['cur_val'],
        'total_reward': total_reward,
        'n_trades':     n_trades,
        'final_units':  info['units_owned']
    }


# ==============================================================================
# SECTION 8: MAIN — TRAINING AND TESTING PIPELINE
# ==============================================================================

# Project Reva — Full DQN training and testing pipeline.

# ── Pipeline ─────────────────────────────────────────────────────────────────
# 1. Generate/load monthly signals + daily sentiment data
# 2. Split 70/30 into train and test sets
# 3. Initialise MultiPropertyEnv, DQNAgent, and state scaler
# 4. Train agent over NUM_EPISODES
# 5. Save model weights, scaler, and portfolio value history
# 6. Switch MODE to 'test' to evaluate on held-out data

# ── Production Integration ────────────────────────────────────────────────────
# Replace generate_synthetic_data() with:

#     # Daily output from your Sentiment Analyzer (runs every day)
#     daily_sentiment = sentiment_model.predict(news_headlines_daily)
#     # shape: (n_months * 30, n_properties)

#     # Monthly outputs from price prediction models
#     monthly_data = {
#         'land_trend':     land_model.predict(location_features),
#         'rental_yield':   rental_model.predict(property_features),
#         'housing_signal': housing_model.predict(comparable_sales),
#     }
#     # Each shape: (n_months, n_properties)

#     property_prices = actual_or_predicted_monthly_prices
#     # shape: (n_months, n_properties)


# ── Config ────────────────────────────────────────────────────────────────
MODELS_FOLDER   = 'reva_models'
REWARDS_FOLDER  = 'reva_rewards'
MODEL_FILE      = 'reva_dqn.weights.h5'
SCALER_FILE     = 'reva_scaler.pkl'

NUM_EPISODES    = 500
BATCH_SIZE      = 32
INITIAL_CAPITAL = 50_000_000    # 50M LKR
N_PROPERTIES    = 3
N_MONTHS        = 120          # 10 years
DAYS_PER_MONTH  = 30
MODE            = 'train'       # 'train' or 'test'

maybe_make_dir(MODELS_FOLDER)
maybe_make_dir(REWARDS_FOLDER)

# ── Step 1: Data ──────────────────────────────────────────────────────────
print("\n[1/5] Generating synthetic market data...")
print("      (Replace with supervised model outputs in production)\n")
monthly_data, daily_sentiment, property_prices = generate_synthetic_data(
    n_properties=N_PROPERTIES, n_months=N_MONTHS,
    days_per_month=DAYS_PER_MONTH, base_price=5_000_000, seed=42
)
print(f"  Monthly signals:   {monthly_data['land_trend'].shape}")
print(f"  Daily sentiment:   {daily_sentiment.shape}")
print(f"  Property prices:   {property_prices.shape}")

# ── Step 2: Split ─────────────────────────────────────────────────────────
print("\n[2/5] Splitting data 70% train / 30% test...")
n_train      = int(N_MONTHS * 0.7)
n_train_days = n_train * DAYS_PER_MONTH

train_monthly   = {k: v[:n_train]         for k, v in monthly_data.items()}
test_monthly    = {k: v[n_train:]         for k, v in monthly_data.items()}
train_sentiment = daily_sentiment[:n_train_days]
test_sentiment  = daily_sentiment[n_train_days:]
train_prices    = property_prices[:n_train]
test_prices     = property_prices[n_train:]
print(f"  Train: {n_train} months | Test: {N_MONTHS - n_train} months")

# ── Step 3: Environment + Agent ───────────────────────────────────────────
print("\n[3/5] Initialising environment and agent...")
env = MultiPropertyEnv(
    monthly_data=train_monthly,
    daily_sentiment=train_sentiment,
    property_prices=train_prices,
    initial_investment=INITIAL_CAPITAL,
    rental_income_rate=0.005,
    transaction_cost_rate=0.02,
    days_per_month=DAYS_PER_MONTH
)
state_size  = env.state_dim
action_size = len(env.action_space)
agent       = DQNAgent(state_size, action_size)
print(f"  State size:  {state_size}  (N*8+1 = {N_PROPERTIES}*8+1)")
print(f"  Action size: {action_size}  (3^{N_PROPERTIES})")

# ── Step 4: Scaler ────────────────────────────────────────────────────────
print("\n[4/5] Fitting state scaler...")
scaler = get_scaler(env)
print("  Done.")

# ── Step 5: Train or Test ─────────────────────────────────────────────────
portfolio_values = []

if MODE == 'test':
    print("\n[5/5] Loading saved model for testing...")
    with open(f'{MODELS_FOLDER}/{SCALER_FILE}', 'rb') as f:
        scaler = pickle.load(f)
    env = MultiPropertyEnv(
        monthly_data=test_monthly, daily_sentiment=test_sentiment,
        property_prices=test_prices, initial_investment=INITIAL_CAPITAL,
        days_per_month=DAYS_PER_MONTH
    )
    agent.epsilon = 0.0
    agent.load(f'{MODELS_FOLDER}/{MODEL_FILE}')

print(f"\n[5/5] Running {NUM_EPISODES} episodes [{MODE.upper()}]...\n")

for ep in tqdm(range(NUM_EPISODES)):
    t0     = datetime.now()
    result = play_one_episode(agent, env, scaler,
                              is_train=(MODE == 'train'),
                              batch_size=BATCH_SIZE)
    dt     = datetime.now() - t0
    portfolio_values.append(result['final_value'])

    if (ep + 1) % 50 == 0:
        print(
            f"  Ep {ep+1:4d}/{NUM_EPISODES} | "
            f"Portfolio: {result['final_value']:>16,.0f} LKR | "
            f"ε: {agent.epsilon:.4f} | "
            f"Trades: {result['n_trades']:3d} | "
            f"Time: {dt}"
        )

# ── Save ──────────────────────────────────────────────────────────────────
if MODE == 'train':
    agent.save(f'{MODELS_FOLDER}/{MODEL_FILE}')
    with open(f'{MODELS_FOLDER}/{SCALER_FILE}', 'wb') as f:
        pickle.dump(scaler, f)

np.save(f'{REWARDS_FOLDER}/{MODE}_portfolio_values.npy',
        np.array(portfolio_values))

# ── Summary ───────────────────────────────────────────────────────────────
v = np.array(portfolio_values)
print(f"\n{'='*65}")
print(f"  Project Reva — {MODE.upper()} Complete")
print(f"{'='*65}")
print(f"  Initial Capital:          {INITIAL_CAPITAL:>20,.0f} LKR")
print(f"  Mean Final Portfolio:     {v.mean():>20,.0f} LKR")
print(f"  Best Episode Portfolio:   {v.max():>20,.0f} LKR")
print(f"  Worst Episode Portfolio:  {v.min():>20,.0f} LKR")
print(f"  Mean Return:              {((v.mean()/INITIAL_CAPITAL)-1)*100:>19.1f} %")
print(f"{'='*65}\n")