---

# 📄 `docs/data_sources.md`

```markdown
# Data Sources – Reva

## 1. Purpose of This Document

This document describes the datasets used in Reva, their sources,
assumptions, and known limitations. Transparency in data usage
is critical for fair evaluation and reproducibility.

---

## 2. Structured Property Data

### Sources

- Public real estate listing platforms
- Manually curated datasets
- Open government or statistical sources (where available)

### Data Types

- Land prices
- House prices
- Rental prices

### Common Attributes

- Location (city / district)
- Size (perches / square feet)
- Property type
- Utilities & amenities

---

## 3. Textual Data for Sentiment Analysis

### Sources

- News articles
- Government announcements
- Real estate blogs
- Public reports

Social media data may be included if accessible and compliant.

---

## 4. Sampling Policy

- Only **small, representative samples** are committed to GitHub
- Full datasets are stored locally or externally
- Samples preserve original schema

This avoids:

- Data leakage
- Legal issues
- Repository bloat

---

## 5. Known Biases & Limitations

### Data Bias

- User-submitted listings may contain noise
- High-end properties may be overrepresented
- Rural data may be sparse

### Temporal Bias

- Historical data may not reflect sudden economic changes
- Sentiment may lag real-world events

---

## 6. Geographical Limitations

- Models are region-specific
- Predictions may not generalize across countries
- Location granularity varies by dataset

---

## 7. Mitigation Strategies

- Feature normalization
- Robust outlier handling
- Sentiment aggregation over time windows
- Explicit documentation of assumptions

---

## 8. Ethical & Privacy Considerations

- No personal user data is used for model training
- All datasets are anonymized
- Models are advisory, not financial guarantees

---

## 9. Future Data Extensions

The system is designed to support:

- Additional regions
- New property types
- Real-time data feeds

All new data sources must be documented here.

---

## 10. Summary

Reva prioritizes **data transparency** and **responsible usage**.
All limitations are acknowledged to ensure realistic expectations
and fair evaluation.
