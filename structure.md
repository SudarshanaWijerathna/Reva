# Project Structure – Reva

This document describes the directory structure of the **Reva – Real Estate Virtual Assistant**
project. It explains the purpose of each folder and important files to ensure clarity,
maintainability, and ease of onboarding for new contributors.

---

## 📁 Root Directory

```text
Reva/
├── README.md
├── structure.md
├── .gitignore
├── requirements.txt
├── docs/
├── data/
├── ml/
├── backend/
├── frontend/
└── scripts/
Root-Level Files
README.md
High-level project overview, goals, and technology stack.

structure.md
(This file) Explains the full folder and file structure of the project.

.gitignore
Prevents committing sensitive, large, or unnecessary files (datasets, models, credentials).

requirements.txt
Python dependencies required for ML models, backend services, and experiments.

📁 docs/ – Project Documentation
Contains all formal documentation required for understanding, evaluation, and reporting.

text
Copy code
docs/
├── architecture.md
├── ai_components.md
├── feature_engineering.md
├── data_sources.md
├── rl_design.md
├── api_contracts.md
└── commit_guidelines.md
Key Files
architecture.md
Overall system architecture, data flow, and layer interactions.

ai_components.md
Description of all AI components, their inputs/outputs, and ownership boundaries.

feature_engineering.md
Detailed explanation of feature derivation, null handling, and transformations.

data_sources.md
Description of datasets used, sources, assumptions, and limitations.

rl_design.md
Reinforcement Learning design: state, action space, reward function, and intuition.

api_contracts.md
Defines communication between frontend, backend, and ML services.

commit_guidelines.md
Rules for Git commit messages and collaboration discipline.

📁 data/ – Data Management & Schemas
This directory contains sample data, processed data, engineered features, and schemas.
It is designed for reproducibility and safe collaboration.

text
Copy code
data/
├── README.md
├── raw/
├── processed/
├── features/
└── schema/
Subdirectories
README.md
Explains data workflow rules, what can/cannot be committed, and reuse guidelines.

raw/
Small, representative samples of raw datasets (never full datasets).

processed/
Cleaned datasets after normalization and sanity checks.

features/
Feature-engineered datasets used for model training and evaluation.

schema/
Dataset schemas defining required columns, types, and constraints.

📁 ml/ – Machine Learning & AI Logic
Contains all AI-related implementations including price models, sentiment analysis,
and reinforcement learning.

text
Copy code
ml/
├── common/
├── land_model/
├── house_model/
├── rental_model/
├── sentiment_model/
└── rl_agent/
Subdirectories
common/
Shared utilities (preprocessing, encoders, metrics).

land_model/
Land price prediction model (training, inference, features).

house_model/
House price prediction model.

rental_model/
Rental price prediction model.

sentiment_model/
Shared NLP model for market sentiment analysis.

rl_agent/
Reinforcement Learning agent for investment decision support.

Each model directory is self-contained and independently evaluable.

📁 backend/ – Server & Business Logic
Implements APIs, authentication, database access, and integration of AI models.

text
Copy code
backend/
├── app.py
├── config.py
├── database/
├── auth/
├── users/
├── properties/
├── predictions/
├── sentiment/
├── rl/
└── utils/
Purpose
Handles HTTP requests

Manages user authentication and data

Serves predictions and recommendations

Acts as a bridge between ML models and frontend

📁 frontend/ – Web Interface
Contains all client-side code for public users and registered users.

text
Copy code
frontend/
├── public/
├── dashboard/
├── assets/
└── index.html
Subdirectories
public/
Pages accessible without login (price prediction, public chatbot).

dashboard/
Authenticated user area (property tracking, analytics, private chatbot).

assets/
CSS, JavaScript, images, and static resources.

📁 scripts/ – Utilities & Experiments
Contains helper scripts and evaluation tools.

text
Copy code
scripts/
├── data_validation.py
├── feature_consistency_check.py
├── sentiment_aggregation.py
└── evaluation_reports.py
These scripts support:

Data quality checks

Feature consistency validation

Aggregating sentiment signals

Generating evaluation summaries

🎯 Design Philosophy
This structure is designed to ensure:

Clear separation of concerns

Independent evaluation of AI components

Easy collaboration and fair assessment

Reproducibility and scalability

Clean academic and industrial presentation
```
