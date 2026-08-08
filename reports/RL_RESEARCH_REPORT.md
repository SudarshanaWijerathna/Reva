# Research Report: Risk-Aware Reinforcement Learning for Reva Real Estate Advisory

## 1. Executive Summary

The current Reva RL component is a Deep Q-Network (DQN) prototype for monthly
real estate portfolio decisions. It represents each of three property categories
with eight features: units owned, four sentiment-derived features, land trend,
rental yield, and housing signal. The agent chooses a joint action from 27
possible combinations of SELL, HOLD, and BUY across the three categories.

The strongest idea in the current architecture is the mixed-frequency design:
daily sentiment is aggregated into monthly decision features while price and
yield signals remain monthly. This is an appropriate architectural insight for
real estate, where transactions are slow but sentiment shocks can occur quickly.

However, the current RL design is closer to a proof-of-concept simulator than a
research-ready decision system. The main research gap is that the agent learns a
return-maximizing policy without explicit treatment of uncertainty, risk,
liquidity, user preferences, causal time alignment, or safe offline evaluation.
For a real estate agent that will advise users about expensive, illiquid assets,
these omissions are not minor engineering details; they define the core research
problem.

This report proposes a novel research direction: Risk and Uncertainty Aware
Personalized Offline Reinforcement Learning for Real Estate Advisory. The core
contribution is to transform the current DQN into a safer, research-grade
advisor that integrates mixed-frequency sentiment, probabilistic price
forecasts, user-specific constraints, transaction frictions, and conservative
offline RL.

## 2. Current System Under Study

### 2.1 Folder-Level Architecture

The RL folder contains these main components:

| File | Role |
| --- | --- |
| `agent.md` | Main documented DQN prototype: replay buffer, sentiment aggregator, environment, DQN agent, training loop. Despite the `.md` extension, it contains executable Python-like code. |
| `sentiment_agg.py` | Production sentiment feature aggregator using cached current sentiment and sentiment history. |
| `prediction_prices.py` | Builds land trend, rental yield, and housing signal features from current and future price cache values. |
| `agent_services.py` | Rebuilds the trained Q-network, loads saved weights and scaler, and exposes inference via `get_recommendation`. |
| `recommendation_api.py` | Builds the production state vector from user portfolio counts, sentiment features, price signals, and a hardcoded cash feature. |
| `routes.py` | FastAPI routes for property signals, sentiment features, state vector, and recommendations. |
| `reva_models/` | Saved DQN weights and scaler artifacts. |

### 2.2 MDP Formulation in the Current Code

The current Markov Decision Process can be summarized as follows:

| MDP Element | Current Design |
| --- | --- |
| State | For each property category: units owned, sentiment current, sentiment trend, sentiment volatility, sentiment shock, land trend, rental yield, housing signal. A normalized cash feature is appended. |
| Action | Joint discrete action across three property categories. Each category can be SELL, HOLD, or BUY, giving `3^3 = 27` actions. |
| Transition | A simulated monthly market episode based on property price arrays and monthly signal arrays. |
| Reward | Portfolio value change plus rental income. |
| Policy model | Two-hidden-layer MLP DQN with replay buffer and epsilon-greedy exploration. |
| Time step | Monthly. |
| Sentiment frequency | Daily input aggregated to monthly state features. |

This is a reasonable first RL framing, but the environment is not yet a faithful
representation of real user advisory behavior. The system chooses high-level
category actions, not specific investable assets, budget allocations, or
personalized purchase/sale recommendations.

## 3. Strengths of the Existing RL Design

1. Mixed-frequency modeling is conceptually strong. The design correctly
recognizes that daily news and market mood may move faster than monthly real
estate transactions.

2. The state vector is simple and interpretable. Each property category receives
the same fixed feature layout, making the model easy to serve and debug.

3. Transaction costs are included. This is essential for real estate because
frequent trading is unrealistic and expensive.

4. Rental income is included in the objective. This aligns the agent with real
estate investment logic, where return comes from both capital appreciation and
cash flow.

5. Production integration exists. The FastAPI routes and model-loading service
show that the RL prototype is intended to support live recommendations rather
than remain isolated in a notebook.

## 4. Critical Technical Analysis

### 4.1 Training and Serving State Mismatch

The training environment dynamically tracks cash as `cash_in_hand /
initial_investment`, while production inference appends a constant `1.0` as the
cash feature. This means every user is served as if they have full normalized
cash availability regardless of actual capital, debt, affordability, or current
liquidity.

The production state uses property counts, not property values, equity, debt,
or investable budget. A user owning one expensive house and another owning one
small land plot can look similar to the model even though their financial
positions are very different.

Research implication: the current agent is not yet personalized portfolio RL.
It is a category-level signal-to-action mapper.

### 4.2 Reward Double Counts Rental Income

In the environment, rental income is added to cash before portfolio value is
computed. The reward then adds rental income again:

`reward = (cur_val - prev_val) + rental_income`

Because `cur_val - prev_val` already includes the rental cash addition, rental
income is counted twice. This biases the policy toward rental-heavy positions
and distorts performance evaluation.

Research implication: the reward must be redesigned before any academic claim
about learned investment quality can be made.

### 4.3 Look-Ahead Leakage Risk

The training observation for month `t` aggregates sentiment up to the end of
month `t` before the action is selected. If the action is interpreted as a
decision made at the start of the month, the agent sees information from the
future. Similarly, synthetic `housing_signal` is derived from actual prices
three months ahead plus noise.

Research implication: without strict temporal alignment, backtest performance
will be optimistically biased.

### 4.4 DQN Stability Limitations

The current DQN uses the same network for action selection and target value
estimation. It does not use a target network, Double DQN, dueling heads,
prioritized replay, distributional value modeling, or conservative offline
regularization. These omissions are especially important because real estate
data is sparse, non-stationary, and expensive to explore in.

Research implication: the current learner is not robust enough for a high-stakes
financial advisory task.

### 4.5 Action Space Is Not Scalable or Realistic

The action space grows as `3^N`. This is manageable for three categories, but
does not scale to many properties, districts, budgets, or investment products.
The action semantics are also too coarse: BUY means buy one unit if affordable,
SELL means sell all units, and HOLD means do nothing. Real advice usually needs
allocation size, affordability constraints, holding period, mortgage/debt
effects, tax effects, and candidate property selection.

Research implication: a hierarchical or constrained action formulation is
needed.

### 4.6 Forecast Uncertainty Is Ignored

The RL state consumes outputs from supervised models as point estimates. It does
not include confidence intervals, predictive variance, model disagreement, or
data freshness. In real estate, forecast uncertainty can dominate expected
return, especially in thin markets or volatile policy environments.

Research implication: the RL agent should reason over forecast distributions,
not only forecast means.

### 4.7 Risk Is Not Explicitly Optimized

The current reward optimizes wealth growth and rental income. It does not
penalize drawdown, concentration, liquidity risk, downside volatility, negative
cash flow, debt exposure, or mismatch with user risk appetite.

Research implication: a real estate advisor should optimize risk-adjusted,
constraint-aware utility rather than raw return alone.

### 4.8 Synthetic Training Pipeline Is Not Research-Ready

The training pipeline in `agent.md` depends on synthetic or externally loaded
prices. The visible code references `prices_loaded`, which is not defined within
the file. Saved model artifacts exist, but the current training provenance is
not reproducible from this folder alone.

Research implication: reproducibility, dataset versioning, baselines, and
walk-forward evaluation must be added.

## 5. Research Gap

Most RL portfolio-management work is designed for liquid financial assets such
as equities or cryptocurrencies, where trades are frequent, transaction costs
are small, and historical price data is dense. Reva operates in a different
domain: real estate is illiquid, high-value, location-sensitive, transaction
costly, slow to rebalance, and strongly affected by policy/news shocks.

The current Reva DQN introduces mixed-frequency sentiment aggregation, but it
does not yet solve the central academic problem:

How can an RL-based real estate advisor learn safe, personalized, and
risk-aware investment recommendations from offline market data while integrating
mixed-frequency sentiment signals and uncertain supervised forecasts?

This gap is academically meaningful because it combines five hard problems:

1. Mixed-frequency decision making: daily sentiment plus monthly/quarterly real
estate signals.
2. Offline RL safety: the agent cannot learn by experimenting with users' real
money.
3. Illiquid asset constraints: high transaction costs, long holding periods,
slow exits, and indivisible purchases.
4. Forecast uncertainty: upstream ML predictions are noisy and should be treated
probabilistically.
5. Personalization: recommendations must depend on user portfolio, cash,
income goal, risk tolerance, horizon, and location preference.

## 6. Proposed Research Direction

### 6.1 Proposed Title

Risk and Uncertainty Aware Personalized Offline Reinforcement Learning for Real
Estate Portfolio Advisory

### 6.2 Core Novelty

The proposed novelty is a mixed-frequency, uncertainty-aware, personalized
offline RL framework for real estate recommendation. Unlike the current DQN,
the proposed system would:

1. Use historical and simulated offline data rather than unsafe online
exploration.
2. Include predictive uncertainty from upstream price, rent, and sentiment
models.
3. Optimize risk-adjusted utility, not only portfolio growth.
4. Enforce affordability, liquidity, concentration, and user-preference
constraints through action masks or constrained policy optimization.
5. Produce explainable recommendations that can justify BUY, HOLD, or SELL
decisions using forecast, sentiment, risk, and portfolio drivers.

### 6.3 Proposed Architecture

The improved architecture should contain six layers:

1. Data layer: historical property prices, rent, land values, macroeconomic
variables, location features, policy/news sentiment, user portfolio history.

2. Forecast layer: supervised models generate probabilistic forecasts for land
price, house price, rent, and sentiment regime. Outputs should include mean,
variance, confidence interval, and data freshness.

3. State construction layer: combine current portfolio value, cash, debt,
property mix, forecast distributions, sentiment features, macro indicators,
transaction cost estimates, user risk profile, and investment horizon.

4. Safety and feasibility layer: mask impossible or unsuitable actions before
the policy acts, for example unaffordable purchases, excessive concentration,
or recommendations violating user constraints.

5. Offline RL layer: train a conservative policy using historical backtests and
scenario-generated market episodes. Candidate algorithms include Conservative
Q-Learning, Implicit Q-Learning, Batch-Constrained Q-Learning, or a Double
Dueling Distributional DQN if the action space remains discrete.

6. Explanation layer: generate user-facing reasons such as "hold because
forecast upside is low relative to transaction cost" or "buy rental property
because expected rental yield is high and downside risk is acceptable."

### 6.4 Revised State Space

The current state should be expanded from category-level counts into a true
personal financial state:

| State Group | Example Features |
| --- | --- |
| Portfolio | market value by asset class, units, unrealized gain, debt, monthly cash flow, concentration ratio |
| Liquidity | available cash, borrowing capacity, emergency reserve, affordability |
| Market forecasts | expected land return, expected rent growth, expected house return, forecast variance, confidence intervals |
| Sentiment | current, trend, volatility, shock, regime probability |
| Macro context | interest rate, inflation, exchange rate, construction cost index, policy regime |
| User profile | risk tolerance, horizon, income preference, location preference, liquidity need |
| Frictions | transaction costs, taxes, estimated time-to-sell, maintenance cost |

### 6.5 Revised Action Space

The current action space can be replaced by one of two research-grade options:

1. Hierarchical action space:
   - High-level policy selects target allocation shift across land, rental, and
     housing.
   - Low-level recommender ranks specific candidate properties.

2. Constrained discrete action space:
   - Actions are generated dynamically from feasible user-specific choices:
     buy candidate property A, sell property B, refinance, hold, or rebalance.
   - Invalid actions are masked before Q-value maximization.

The hierarchical approach is more scalable and more realistic for a real estate
agent because it separates portfolio strategy from property selection.

### 6.6 Revised Reward Function

A research-grade reward should optimize user utility:

`reward = net_wealth_change + rental_cashflow - transaction_costs - tax_costs - risk_penalty - liquidity_penalty - concentration_penalty`

Recommended risk terms:

| Risk Term | Purpose |
| --- | --- |
| Drawdown penalty | Discourages policies that expose users to large losses. |
| CVaR penalty | Penalizes tail risk, not only average volatility. |
| Liquidity penalty | Accounts for slow exit from real estate positions. |
| Concentration penalty | Prevents overexposure to one property type or location. |
| Affordability penalty | Avoids recommendations that damage cash reserves. |

The reward should be normalized, for example as percentage change in net worth,
so training is not dominated by absolute LKR scale.

## 7. Research Questions

RQ1: Does mixed-frequency sentiment aggregation improve real estate portfolio
recommendation performance compared with monthly sentiment averages?

RQ2: Does uncertainty-aware offline RL reduce downside risk compared with the
current DQN and rule-based baselines?

RQ3: How much does personalization, including user cash, risk tolerance, and
portfolio composition, improve recommendation feasibility and utility?

RQ4: Can conservative offline RL produce safer recommendations than standard
DQN under non-stationary real estate market regimes?

RQ5: Which explanation factors most strongly affect trust in RL-generated real
estate advice: forecast return, sentiment, risk, cash flow, or affordability?

## 8. Experimental Methodology

### 8.1 Datasets

The study should use:

1. Historical Sri Lankan property prices by category and location.
2. Rental price histories and rental yield estimates.
3. Land price histories.
4. Daily or weekly sentiment extracted from real estate news, policy news, and
macroeconomic news.
5. Macroeconomic variables such as interest rates, inflation, exchange rates,
construction costs, and policy events.
6. Synthetic user portfolios generated from realistic wealth, income, risk, and
holding patterns.

If real transaction data is limited, the study can use scenario simulation, but
the simulator must be calibrated against historical data and evaluated under
walk-forward splits.

### 8.2 Baselines

The proposed method should be compared against:

1. Buy-and-hold portfolio.
2. Rule-based strategy using forecast thresholds.
3. Mean-variance or risk-parity allocation.
4. Supervised ranking model without RL.
5. Current Reva DQN.
6. DQN without sentiment features.
7. DQN with monthly average sentiment only.
8. Conservative offline RL without personalization.

### 8.3 Metrics

Performance should not be measured only by final portfolio value. Recommended
metrics include:

| Metric | Why It Matters |
| --- | --- |
| Net worth growth | Captures wealth creation. |
| Rental cash flow | Measures income generation. |
| Sharpe or Sortino ratio | Measures risk-adjusted return. |
| Maximum drawdown | Captures severe losses. |
| CVaR | Measures tail risk. |
| Turnover | Measures excessive trading. |
| Transaction cost paid | Important in real estate. |
| Feasibility rate | Percentage of recommendations that users can actually execute. |
| Regret versus hindsight policy | Measures decision quality. |
| Explanation fidelity | Tests whether explanations match model drivers. |

### 8.4 Evaluation Protocol

Use walk-forward time-series validation:

1. Train on early historical periods.
2. Validate on the next period.
3. Test on future unseen periods.
4. Repeat over multiple market regimes.

Stress tests should include:

1. Interest-rate shocks.
2. Political sentiment shocks.
3. Rental market downturns.
4. Property price stagnation.
5. Liquidity-constrained users.
6. High transaction cost scenarios.

### 8.5 Ablation Studies

Recommended ablations:

1. Remove sentiment features.
2. Replace sentiment current/trend/volatility/shock with monthly average only.
3. Remove uncertainty features.
4. Remove risk penalty.
5. Remove user personalization.
6. Remove action masks.
7. Replace offline conservative RL with standard DQN.

These ablations will show which components contribute actual research value.

## 9. Implementation Roadmap

### Phase 1: Correctness and Reproducibility

1. Convert `agent.md` into a proper Python module or separate documentation from
code.
2. Fix reward double counting of rental income.
3. Remove time leakage from sentiment and forecast features.
4. Replace undefined training inputs with reproducible dataset loading.
5. Add training metadata: dataset version, seed, hyperparameters, and metrics.
6. Add unit tests for state construction, reward calculation, action mapping,
and sentiment aggregation.

### Phase 2: Research-Grade DQN Baseline

1. Add target network.
2. Add Double DQN update.
3. Add action masks for invalid actions.
4. Normalize rewards.
5. Add baselines and walk-forward evaluation.
6. Log Sharpe, drawdown, turnover, and CVaR.

### Phase 3: Risk-Aware Personalization

1. Add user cash, debt, risk tolerance, horizon, and income preference to state.
2. Redesign reward around risk-adjusted user utility.
3. Include transaction taxes, maintenance, liquidity, and concentration risk.
4. Add explanations for each recommendation.

### Phase 4: Offline RL and Uncertainty

1. Convert supervised model outputs into probabilistic forecasts.
2. Add forecast uncertainty to the RL state.
3. Train conservative offline RL policies.
4. Add uncertainty gates that return HOLD or "needs review" when model
confidence is too low.
5. Evaluate under historical and stress-test scenarios.

## 10. Expected Academic Contributions

This work can claim the following contributions if implemented and evaluated:

1. A mixed-frequency real estate RL framework combining daily sentiment dynamics
with monthly property forecasts.

2. A risk-aware offline RL formulation for illiquid property portfolio
recommendation.

3. A personalization mechanism that conditions real estate advice on user
portfolio, liquidity, horizon, and risk appetite.

4. An uncertainty-aware decision layer that propagates upstream forecast
confidence into RL recommendations.

5. A practical evaluation protocol for real estate RL using walk-forward
backtesting, stress testing, and feasibility metrics.

## 11. Recommended Final Research Problem Statement

This research investigates how mixed-frequency sentiment signals, probabilistic
property forecasts, and user-specific financial constraints can be integrated
into a conservative offline reinforcement learning framework to generate safe,
explainable, and personalized real estate investment recommendations.

The proposed solution addresses the gap between standard portfolio RL methods,
which assume liquid and frequently traded assets, and real estate advisory,
where assets are illiquid, costly to transact, difficult to value, and deeply
dependent on individual user constraints.

## 12. Conclusion

The current Reva RL module is a useful foundation, especially because it already
introduces daily-to-monthly sentiment aggregation and a deployable DQN inference
path. Its main limitation is not that it uses DQN; it is that the surrounding
MDP does not yet represent the true advisory problem. A real estate agent must
make personalized, feasible, risk-aware, uncertainty-aware recommendations
under offline learning constraints.

The strongest research opportunity is therefore to evolve Reva from a
return-seeking DQN prototype into a risk-aware, uncertainty-aware, personalized
offline RL advisor for illiquid real estate assets. This direction is novel,
academically defensible, and closely aligned with the project's goal of acting
like a real-world real estate agent rather than a simple price-prediction
service.

## 13. Foundational Literature to Position the Work

These references can be used to frame the study:

1. Markowitz, H. (1952). Portfolio Selection. Journal of Finance.
2. Mnih, V. et al. (2015). Human-level control through deep reinforcement
learning. Nature.
3. van Hasselt, H., Guez, A., and Silver, D. (2016). Deep Reinforcement
Learning with Double Q-learning.
4. Schaul, T. et al. (2016). Prioritized Experience Replay.
5. Bellemare, M. G., Dabney, W., and Munos, R. (2017). A Distributional
Perspective on Reinforcement Learning.
6. Kumar, A. et al. (2020). Conservative Q-Learning for Offline Reinforcement
Learning.
7. Kostrikov, I., Nair, A., and Levine, S. (2021). Offline Reinforcement
Learning with Implicit Q-Learning.

