4. Data Flow
Step 1: Data Ingestion

Structured property data (size, location, type)

Textual data (news, reports, social media)

Step 2: Feature Engineering

Numeric features derived from structured data

Sentiment features derived from text

All transformations documented and reproducible

Step 3: Prediction

One of the three price models is selected based on property type

Output: predicted price and trend

Step 4: Decision Support

RL agent consumes:

predicted prices

price trends

sentiment signals

Output: buy / hold / sell recommendation

Step 5: Presentation

Price predictions visualized

Market sentiment displayed separately

Recommendations explained in natural language

5. Design Principles

Modularity: Each AI component is independent

Explainability: No black-box price manipulation

Reproducibility: All data and features are documented

Scalability: New models or datasets can be added easily

Fair Evaluation: Clear ownership of AI components

6. Public vs Authenticated Mode
Public Mode

Price prediction

General sentiment insight

No data storage

Authenticated Mode

Property tracking

Historical predictions

Personalized investment advice

Private chatbot access