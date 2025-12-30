# Feature derivation & null handling# Feature Engineering – Reva

## 1. Purpose of This Document

This document describes the **feature engineering strategy** used in the Reva project.
It explains how raw property data is transformed into meaningful, model-ready features
in a **consistent, reproducible, and explainable** manner.

The goal is to ensure that:
- All models use well-defined features
- Feature logic is reusable for new datasets
- Null values and outliers are handled consistently
- Supervisors and contributors can audit decisions easily

---

## 2. General Feature Engineering Philosophy

Reva follows these core principles:

1. **Domain-driven features**  
   Features are derived based on real estate domain knowledge, not blind automation.

2. **Separation of concerns**  
   - Raw data → cleaning  
   - Cleaning → feature derivation  
   - Features → modeling  

3. **Reproducibility**  
   The same transformations must apply to future datasets.

4. **Explainability**  
   Every feature must have a clear meaning and justification.

---

## 3. Feature Categories

Across all price models, features fall into the following categories:

- Location-based features
- Property-specific features
- Accessibility & infrastructure features
- Market & temporal features
- Sentiment-derived features (optional)
- Derived composite features

---

## 4. Land Price Model – Feature Design

### 4.1 Raw Inputs
- Land size (perches / sqm)
- District / city
- Availability of utilities
- Road access information

### 4.2 Engineered Features

| Feature Name | Description | Type |
|-------------|-------------|------|
| `land_size_perches` | Normalized land size | Numeric |
| `distance_to_city_km` | Distance to nearest major city | Numeric |
| `road_access_score` | Proximity-weighted road access | Numeric |
| `utility_score` | Combined electricity + water availability | Numeric |
| `location_score` | Composite city + road influence score | Numeric |

### 4.3 Composite Feature Logic
- `location_score` combines:
  - city distance decay
  - road accessibility
- Exponential or capped decay functions are used to avoid linear bias.

---

## 5. House Price Model – Feature Design

### 5.1 Raw Inputs
- Floor area
- Number of rooms
- Property age
- Location attributes

### 5.2 Engineered Features

| Feature Name | Description |
|-------------|------------|
| `price_per_sqft` | Historical normalization feature |
| `room_density` | Rooms per square foot |
| `house_age_bucket` | Age grouped into bins |
| `location_score` | Shared location feature |

---

## 6. Rental Price Model – Feature Design

### 6.1 Raw Inputs
- Property type
- Floor area
- Furnishing status
- Location

### 6.2 Engineered Features

| Feature Name | Description |
|-------------|------------|
| `rent_per_sqft` | Area-normalized rent |
| `demand_score` | Derived from location & amenities |
| `employment_sentiment` | Optional sentiment feature |
| `urban_access_score` | City proximity |

---

## 7. Sentiment-Derived Features (Shared)

Sentiment is treated as an **external signal**, not a direct price modifier.

### 7.1 Sentiment Outputs

| Feature | Description |
|------|------------|
| `sentiment_score` | Normalized score (-1 to +1) |
| `sentiment_label` | Positive / Neutral / Negative |
| `sentiment_volatility` | Rate of sentiment change |

### 7.2 Model-Specific Usage

- **Land**: infrastructure & policy sentiment  
- **House**: economic & interest rate sentiment  
- **Rental**: employment & tourism sentiment  

Sentiment features are **optional** and evaluated via ablation studies.

---

## 8. Temporal Feature Handling

Temporal information is encoded as:

- Year
- Quarter
- Relative age (e.g., years since listing)

This avoids overfitting while capturing long-term trends.

---

## 9. Null Value Handling Strategy

Null handling is **explicit and documented**, not implicit.

| Feature Type | Strategy | Justification |
|-------------|---------|---------------|
| Numerical | Median imputation | Robust to outliers |
| Categorical | "Unknown" category | Preserve information |
| Boolean | Default = False | Conservative assumption |
| Derived features | Recomputed if possible | Avoid noise |

Null-handling logic must remain **consistent across datasets**.

---

## 10. Outlier Handling

Outliers are handled using:

- Log transformation for price-related features
- Percentile capping (1%–99%)
- Domain-based filtering (invalid values removed)

Outlier rules are applied **before model training**.

---

## 11. Feature Scaling & Encoding

- Tree-based models: minimal scaling required
- Linear models: standard scaling applied
- Categorical features:
  - One-hot encoding
  - Frequency encoding (where appropriate)

Encoders are saved and reused to prevent data leakage.

---

## 12. Feature Versioning

Feature sets are versioned to ensure traceability.

Example:
```text
land_features_v1.csv
land_features_v2.csv
