# Project Reva 

Reva is a Real Estate Virtual Assistant that uses Machine Learning
to predict land, house, and rental prices.

## Goals
- ML-powered price prediction
- Clean web interface
- Real-world data handling
- Educational & portfolio-ready project

## Tech Stack (Planned)
- Python (ML & backend)
- LightGBM / XGBoost
- HTML, CSS, JavaScript
- Git & GitHub for version control

## Sentiment
- Mongo db IP address configure
- Run kb_initializer
- Run run_both in threads
- Run sentiment_aggregate.add_pipe

## Backend

# Auth
routes
- sign up 
- log in
Utilities
- Autherize
- create access token
- validate user token
- Hashing

# Users
routes
- get user profle
- create user profile
- update user profile
- update investmens preferances

# properties
routes
- add housing
- add rental 
- add land
Services
- create/buy housing property
- create/buy rental property
- create/buy land property

# portfolio
routes
- get summery
- get properties
- get insight 
services
- get properties and portfolio summery (growth, tot profit, property mix)

## Portfolio valuation V2

Use `PORTFOLIO_VALUATION_ENGINE=hybrid` for the evidence-based portfolio path.

- **Estimated Value** is the property ML model's total-value anchor multiplied by
  a matched, observed market-index ratio. Forecast index values are never called
  a current value.
- Land purchase price is entered as LKR per perch, but the portfolio displays and
  accounts for the total land cost (`price per perch × land size`).
- **Unrealized Gain** is `estimated value - purchase price - acquisition costs -
  capital improvements`.
- **Total Return** adds recorded net rental cash flow. Sold-property proceeds and
  costs are recorded separately through the transaction ledger.
- Rental income is calculated by inclusive calendar months from lease start through
  the current month, using the agreed monthly rent for each lease period. The rent
  change/end date is the boundary; edit the property with the new rent and new
  start date when the agreement changes, and the previous period is retained.
- CBSL asking-price indices currently cover Colombo district. Properties outside
  Colombo remain at their model anchor and are labelled `anchor_only`; the system
  does not silently apply Colombo movement nationally.
- A property missing a required model input is labelled `unavailable`. Edit the
  property to add its district and physical features instead of accepting an
  invented default.

The properties API includes `valuation_as_of`, status, confidence, range,
model/index versions, factor, notes, and provenance. Optional `as_of=YYYY-MM-DD`
is supported by portfolio summary/property routes. Quarterly snapshots and the
property transaction ledger are exposed under `/api/portfolio/snapshots` and
`/api/portfolio/properties/{property_id}/transactions`.

Observed CBSL updates are stored separately from the frozen LSTM training CSV.
Keep `LSTM_INDEX_ENABLED=false` unless a retrained forecast model beats the naive
benchmark in out-of-time tests.

# predictions
utils
- get insight
- get market price

# Deploy
- frontend | Root - frontend |npm install ->  npm run dev
- Backend   | Root- Reva |  uvicorn backend.app:app --reload
- ML services | see docs/local_model_services.md
- WSL | `sudo apt update && sudo apt install redis-server`, then `sudo service redis-server start`
- Redis is an optional cache for portfolio valuation; without it, the backend recomputes values.
