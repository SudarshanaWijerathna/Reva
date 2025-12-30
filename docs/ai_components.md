
---

# `docs/ai_components.md`

```markdown
# AI Components & Responsibilities – Reva

## 1. Purpose of This Document

This document defines:
- All AI components in the Reva system
- Their responsibilities
- Their inputs and outputs
- Ownership boundaries for fair evaluation

Each component is designed to be **independent, testable, and explainable**.

---

## 2. AI Components Overview

| Component | Type | Purpose |
|--------|------|--------|
| Land Price Model | Regression | Predict land value |
| House Price Model | Regression | Predict house value |
| Rental Price Model | Regression | Predict rental rates |
| Sentiment Model | NLP | Analyze market sentiment |
| RL Agent | Reinforcement Learning | Recommend actions |

---

## 3. Land Price Prediction Model

### Responsibility
- Predict land price based on location, size, and infrastructure factors

### Inputs
- Engineered numeric features
- Optional sentiment features (policy, infrastructure)

### Outputs
- Predicted land price
- Price trend indicator

### Notes
- Does NOT perform sentiment analysis
- Does NOT make decisions

---

## 4. House Price Prediction Model

### Responsibility
- Predict residential house prices

### Inputs
- Structural features (size, rooms)
- Location-based features
- Optional economic sentiment

### Outputs
- Predicted house price
- Price confidence range (optional)

---

## 5. Rental Price Prediction Model

### Responsibility
- Predict expected rental income

### Inputs
- Property attributes
- Demand-related features
- Optional employment / tourism sentiment

### Outputs
- Predicted rental value
- Demand indicator

---

## 6. Sentiment Analysis Model (Shared Component)

### Responsibility
- Analyze real-estate-related textual data
- Capture public and market perception

### Data Sources
- News articles
- Government reports
- Social media (if available)

### Outputs
- `sentiment_score` (numeric)
- `sentiment_label` (positive / neutral / negative)
- Topic-aware sentiment signals

### Key Design Choice
- **Single shared sentiment model**
- Different models consume different sentiment views
- Avoids duplication and inconsistency

---

## 7. Reinforcement Learning (RL) Agent

### Responsibility
- Provide decision support (not price prediction)
- Learn optimal investment strategies

### State Representation
- Predicted price
- Price trend
- Market sentiment
- Property attributes

### Action Space
- BUY
- HOLD
- SELL

### Reward Function
- Based on simulated return on investment
- Adjusted lightly by sentiment signals

### Output
- Recommended action
- Expected return (qualitative)

---

## 8. Interaction Between Components

- Price models and sentiment model operate independently
- RL agent consumes their outputs
- No model directly modifies another model’s predictions

This ensures:
- Interpretability
- Clean evaluation
- Modular experimentation

---

## 9. Evaluation Strategy

Each AI component is evaluated independently:
- Price models → regression metrics
- Sentiment model → classification accuracy / polarity
- RL agent → cumulative reward and policy stability

---

## 10. Final Note

This separation of AI responsibilities ensures that Reva remains:
- Academically sound
- Engineering-friendly
- Scalable
- Fairly assessable across team members
