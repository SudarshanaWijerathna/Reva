# Reinforcement Learning Design – Reva

## 1. Purpose of the RL Component

The Reinforcement Learning (RL) component in Reva acts as a **decision-support layer**.
It does **not** predict prices. Instead, it learns optimal **investment actions**
based on predicted prices, market trends, and sentiment signals.

The RL agent answers:
- Should a user **buy**, **hold**, or **sell** a property?
- Which action maximizes long-term return under current market conditions?

---

## 2. RL Problem Formulation

| Element | Description |
|------|-------------|
| Environment | Simulated real estate market |
| Agent | Investment decision-maker |
| State | Market & property signals |
| Actions | Buy / Hold / Sell |
| Reward | Investment return proxy |

The problem is formulated as a **Markov Decision Process (MDP)**.

---

## 3. State Representation

The state captures information available at a decision point.

### State Variables

| Feature | Description |
|------|-------------|
| `predicted_price` | Output from price model |
| `previous_price` | Last known price |
| `price_trend` | Relative change over time |
| `sentiment_score` | Market sentiment (-1 to +1) |
| `property_type` | Land / House / Rental |
| `location_score` | Composite location indicator |

### Example State Vector

```text
[12.5M, 11.8M, +6%, +0.4, HOUSE, 0.72]
