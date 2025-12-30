# Data Directory – Reva 🗂️

This directory contains all data-related assets used in the Reva project.
The goal of this structure is to ensure **reproducibility, clarity, and safe collaboration**
while supporting multiple machine learning models.

This folder is **not just for storing data**, but for documenting **how data is transformed**
from raw inputs into model-ready features.

---

## 📁 Directory Structure

```text
data/
├── raw/                        # Sample raw datasets (unprocessed)
|   ├── land_prices_sample.csv
|   ├── house_prices_sample.csv
|   └── rental_prices_sample.csv
├── processed/                  # Cleaned & standardized datasets
|   ├── land_cleaned.csv
|   ├── house_cleaned.csv
|   └── rental_cleaned.csv
├── features/                   # Feature-engineered datasets
|   ├── land_features_v1.csv
|   ├── house_features_v1.csv
|   └── rental_features_v1.csv
├── schema/                     # Documentation & schemas
data/schema/
|   ├── land_schema.md
|   ├── house_schema.md
|   └── rental_schema.md
└── README.md                   # This file
