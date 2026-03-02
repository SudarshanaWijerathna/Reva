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

# predictions
utils
- get insight
- get market price

# Deploy
- frontend | Root - frontend |npm install ->  npm run dev
- Backend   | Root- Reva |  uvicorn backend.app:app --reload    
- WSL | sudo service redis-server start