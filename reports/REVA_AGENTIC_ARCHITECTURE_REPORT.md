# Academic Report: Reva as an Agentic Real Estate Advisory System

## 1. Executive Summary

Reva is evolving from a real estate price prediction platform into an
agentic real estate advisory system. The target vision is a digital agent that
can behave like a real-world real estate advisor: it should understand a
user's property portfolio, estimate current and future values, interpret market
sentiment, recommend investment actions, and communicate those recommendations
through natural conversation and visual interfaces.

The current project already contains many foundations for this vision:

- A React frontend with public prediction pages, an authenticated dashboard,
  an Ask Reva chatbot, portfolio tracking, map exploration, and admin panels.
- A FastAPI backend with authentication, user profile management, property
  storage, portfolio summaries, dynamic feature definitions, prediction
  history, model registry, and chatbot routing.
- Independent model services for land and house price prediction, with a
  rental prediction service scaffold prepared for future development.
- A sentiment analysis subsystem that collects real estate/market text,
  applies FinBERT-style sentiment analysis, semantically filters documents,
  aggregates market sentiment, and exposes the result through Redis-backed
  cache services.
- A previous reinforcement learning research/design direction for investment
  recommendation, although the current inspected source snapshot does not
  contain an active mounted RL API implementation.

The main conclusion is that Reva currently behaves as a collection of
intelligent services, not yet as a single coherent agent. The next academic and
engineering opportunity is to introduce an agentic orchestration layer that
connects perception, memory, tool use, planning, decision policy, explanation,
and feedback learning.

This report critically analyzes the current whole-project architecture and
proposes a research-grade agentic architecture organized around four agent
characteristics: situatedness, sociability, autonomy, and adaptability.

## 2. Project Vision

The intended system can be defined as:

> Reva is an intelligent real estate agent for the Sri Lankan property market
> that supports users in valuation, portfolio management, forecasting,
> sentiment-aware investment analysis, and personalized buy/hold/sell
> recommendations.

This vision is stronger than a standard prediction application. A price
prediction system answers isolated questions such as "What is this property
worth?" An agentic real estate advisor should answer broader situated questions
such as:

- "Is this land a good investment for my current portfolio?"
- "Should I sell one property and buy another?"
- "How has market sentiment changed for rentals?"
- "What is the risk if I buy now?"
- "Which investment action best matches my budget, time horizon, and risk
  tolerance?"

Therefore, the academic framing should treat Reva as an agentic
decision-support architecture rather than only as a machine learning platform.

## 3. Current System Architecture

### 3.1 High-Level Components

| Layer | Current Implementation | Main Function |
| --- | --- | --- |
| Frontend | React/Vite application | User interaction, prediction forms, chatbot, dashboard, admin UI |
| Backend API | FastAPI application | Authentication, routing, database access, prediction orchestration |
| Data persistence | SQLAlchemy with SQLite/PostgreSQL support | Users, profiles, properties, preferences, dynamic features, prediction records, model registry |
| Model services | `ml/land_service`, `ml/house_service`, `ml/rental_service` | Independent prediction services |
| Sentiment subsystem | `Sentiment/Analysis` pipeline | Collect, filter, score, aggregate, and cache market sentiment |
| Portfolio layer | `backend/portfolio` | Summarize user holdings and property mix |
| Admin governance | `backend/admin`, frontend admin panel | Manage features, users, model registry, metrics, active model selection |
| Chat interface | `/ask` endpoint and `Askreva.tsx` | Natural-language interaction with Reva |
| RL/recommendation layer | Design/report exists; current source snapshot contains no active mounted RL service | Planned decision layer for buy/hold/sell advice |

### 3.2 Conceptual Data Flow

```text
User input / property data / chat message
        |
        v
Frontend interface
        |
        v
FastAPI backend
        |
        +--> Authentication and user context
        +--> Portfolio database and preferences
        +--> Dynamic feature validation
        +--> Active model registry
        +--> Land / house / rental model services
        +--> Sentiment cache and sentiment pipeline
        +--> Recommendation layer
        |
        v
Prediction, portfolio insight, sentiment insight, or recommendation
        |
        v
Frontend explanation through dashboard, forms, charts, or chatbot
```

The architecture is modular and service-oriented. This is a strong basis for
agentic development because an agent can later treat each subsystem as a tool.

## 4. Backend Analysis

### 4.1 API Composition

The backend entry point is `backend/app.py`. It creates a FastAPI application,
loads environment variables, configures CORS, creates database tables, and
mounts routers for:

- Authentication.
- User account operations.
- Property creation.
- Portfolio summary and insights.
- Dynamic features.
- Dynamic predictions.
- Admin model and feature management.

The backend also exposes `/ask`, which sends user messages to Gemini with a
system prompt designed to trigger special response formats for prediction
forms, prediction results, and graphs.

### 4.2 User and Property Memory

The backend stores:

- User accounts.
- User profiles.
- Investment preferences.
- Property records for housing, rental, and land.
- Purchase price, purchase date, type, location, and type-specific fields.

This is the beginning of long-term agent memory. A real-world real estate
agent remembers what a client owns, what they prefer, how much risk they can
tolerate, and what they asked previously. Reva has the first pieces of this
memory, but does not yet use all of it in decision making.

### 4.3 Portfolio Intelligence

The portfolio service calculates:

- Total investment.
- Current portfolio value.
- Growth percentage.
- Total profit.
- Property mix.
- Property-level sentiment labels.
- A simple natural-language insight.

This gives the system a situated view of the user. However, current portfolio
valuation is limited by a placeholder current-market-price function that
returns a constant value. For the real estate agent vision, this must be
connected to the active prediction models, valuation cache, or reliable
market-price service.

### 4.4 Dynamic Feature and Prediction Layer

The dynamic feature system is one of the strongest architectural decisions in
the project. It lets admins define model-specific feature schemas for land,
house, and rental models. The frontend can fetch those active feature
definitions and dynamically render prediction forms.

The dynamic prediction endpoint:

1. Retrieves active feature definitions.
2. Validates input feature types.
3. Resolves the active model for a given model type.
4. Calls the deployed model endpoint.
5. Stores prediction records for the user.

This is important for adaptability. A future Reva agent can change model
versions or feature sets without rewriting the frontend.

### 4.5 Admin Model Registry

The admin model registry stores:

- Model name.
- Model type: land, house, or rental.
- Version.
- Deployed endpoint.
- Artifact URL.
- Performance notes.
- MAE, RMSE, R2, and MAPE.
- Active/inactive status.

Only one model per type should be active. This is useful for model governance,
auditing, and controlled deployment. In an agentic architecture, the model
registry becomes the agent's tool directory: the agent can choose the currently
approved valuation tool for each property type.

### 4.6 Backend Limitations

The backend is modular, but several critical gaps remain:

1. The chatbot endpoint uses prompt-trigger strings rather than robust
   structured tool calls.

2. The chatbot can return a `[PREDICTION_RESULT]` directly from the language
   model prompt, meaning a valuation may be generated conversationally rather
   than through the trained model service.

3. The RL/recommendation route is not mounted in the inspected `app.py`, and
   the inspected current `backend/rl/recommendation_api.py` is empty. Therefore,
   investment recommendation currently exists more as a research/design
   direction than as an active production feature in this source snapshot.

4. User investment preferences exist in the database model, but they are not
   deeply used in prediction, portfolio, or recommendation logic.

5. Current portfolio valuation still uses placeholder logic.

6. Google authentication is implemented on the frontend by storing a Google
   OAuth access token, but the backend JWT-protected routes expect Reva-issued
   JWTs. This creates an authentication mismatch for authenticated features.

7. Admin authorization is based on a configured admin email rather than a
   database role model.

8. Database naming is confusing: Pydantic models and SQLAlchemy ORM schemas are
   split across files with names that may mislead future maintainers.

## 5. Frontend Analysis

### 5.1 User Interfaces

The frontend provides several interaction modes:

- Home page explaining Reva and routing users to predictions.
- Ask Reva chatbot.
- Land, house, and rental prediction pages.
- Portfolio dashboard.
- Add-property modal.
- Admin dashboard.
- Feature management panel.
- Model management panel.
- Map explorer.

This is a strong user-facing foundation for a real estate assistant. The
system is not only analytical; it is already designed around user workflows.

### 5.2 Ask Reva Chatbot

The Ask Reva page supports:

- Free-form text messages.
- Suggestions for house, rental, and land predictions.
- Bot typing indicator.
- Prediction form cards.
- Prediction result cards.
- Graph messages.
- A previous-chat sidebar placeholder.

The chatbot is an important sociability layer. It lets Reva interact in
natural language instead of forcing users through forms only.

However, the current chatbot is not yet a full agent. It relies on specific
response markers such as:

- `[TRIGGER_PREDICTION_FORM]`
- `[PREDICTION_RESULT]`
- `[TRIGGER_GRAPH]`

This is useful for prototyping, but brittle for a research-grade agentic
system. A mature architecture should route extracted intents to actual tools:
prediction service, portfolio service, sentiment service, recommendation
service, chart service, and explanation service.

### 5.3 Prediction Pages

The land, house, and rental pages dynamically load active feature definitions
and call the backend prediction endpoint. This supports model evolution and
separates UI from model schema.

Land also includes a more customized form with fields such as land size,
district, location, utilities, road access, and distance to town. This aligns
well with real estate domain knowledge.

### 5.4 Portfolio Dashboard

The dashboard gives authenticated users:

- Portfolio value.
- Total profit.
- Sentiment.
- Property mix.
- Reva insight.
- Property table.
- Add-property workflow.

This dashboard is the closest current feature to a real-world real estate
agent's client file. It gives Reva memory of user assets and an interface for
monitoring changes over time.

### 5.5 Frontend Limitations

Important limitations include:

1. The map explorer currently simulates nearest-record data rather than calling
   a real market-data endpoint.

2. The previous-chat sidebar is not yet connected to persistent conversation
   history.

3. Prediction charts use generated/mock bar values derived from the prediction
   rather than verified historical time-series outputs.

4. The frontend navbar imports CSS using an absolute local machine path, which
   weakens portability.

5. Chatbot predictions are not consistently connected to the dynamic prediction
   service.

6. Review/feedback UI appears mostly static and does not yet feed an
   adaptation loop.

## 6. Model Services Analysis

### 6.1 Land Model Service

The land service is mature relative to the other model services. It:

- Runs as an independent FastAPI service.
- Loads a Joblib model bundle.
- Applies domain-specific feature engineering.
- Uses geocoding and distance-to-Colombo features.
- Encodes utilities, road access, text mentions, district, location, and land
  type.
- Applies district-level land valuation index calibration across time periods.

This is a strong foundation for situated valuation because it uses location
intelligence rather than raw tabular input only.

### 6.2 House Model Service

The house service:

- Runs as an independent FastAPI service.
- Loads a CatBoost model artifact.
- Validates required fields.
- Normalizes house and land square footage.
- Uses structural features, geographic coordinates, district, sub-location,
  and posting date.
- Returns total predicted value and price per square foot.

This service is a useful pattern for the future rental model. It has a cleaner
artifact-loading and request-validation shape than several backend adapters.

### 6.3 Rental Model Service

The rental service is currently a scaffold:

- It exposes `/health` and `/predict`.
- It checks whether `model.joblib` exists and has non-zero size.
- The inspected `model.joblib` is empty.
- When no model is available, the service reports degraded readiness.

This is good engineering behavior because the service fails explicitly rather
than pretending the model exists. As the user noted, the rental model can be
developed in the same pattern as the house model: validated inputs, trained
artifact, feature normalization, consistent response schema, and independent
deployment.

### 6.4 Model Layer Limitations

The model layer has several research and engineering gaps:

1. The model services return point estimates, not uncertainty intervals.

2. The frontend sometimes creates a naive +/- 10 percent range, but this is not
   calibrated model uncertainty.

3. The model registry records performance metrics, but the live prediction path
   does not expose confidence, data freshness, or model version to the user.

4. Rental prediction is not yet trained.

5. There is no unified feature-store contract guaranteeing that frontend,
   backend, and model services share exactly the same feature names and units.

6. Current-price prediction for owned portfolio properties is not yet fully
   connected to the model services.

## 7. Sentiment System Analysis

The sentiment subsystem is a substantial component and contributes directly to
agent situatedness.

### 7.1 Current Sentiment Pipeline

The pipeline contains:

- Data collection from APIs, news scraping, and web scraping.
- Text cleaning.
- FinBERT-based sentiment classification.
- Semantic filtering using embeddings and similarity against reference
  knowledge bases.
- Property-type relevance scoring for land, house, and rental markets.
- Short-, medium-, and long-term relevance scoring.
- MongoDB storage.
- Aggregation into property-level sentiment labels and scores.
- Redis caching for backend access.
- Scheduler support for periodic cache and pipeline updates.

This gives Reva a market-awareness layer. A real real estate agent reads news,
policy changes, infrastructure announcements, and investor sentiment. Reva's
sentiment pipeline is the computational version of that behavior.

### 7.2 Sentiment Limitations

Several issues should be addressed before research-grade claims:

1. The sentiment query currently appears generic in places, for example "stock
   market headlines", rather than clearly real-estate-specific.

2. The relevant document fetch function queries `"relevance": "noise"` even
   though its name suggests relevant documents. This may invert the intended
   filtering logic.

3. A variable named `five_years_ago` uses a two-day cutoff in the inspected
   aggregation pipe, which indicates unclear time-window semantics.

4. Some reference knowledge-base examples are generic financial-market text,
   not specifically Sri Lankan real estate.

5. Sentiment outputs are not yet deeply integrated into a final agentic
   decision process, except through dashboard labels and prior RL design ideas.

## 8. RL and Recommendation Layer

The earlier RL-focused analysis identified a DQN-based research direction for
buy/hold/sell recommendations using:

- Portfolio state.
- Sentiment current, trend, volatility, and shock features.
- Land price trend.
- Rental yield.
- Housing signal.
- Cash state.
- Joint actions across property types.

In the current inspected source snapshot, however, the active `backend/rl`
folder contains an empty `recommendation_api.py` and the previously produced
research report. The RL layer should therefore be treated as a planned or
research-stage decision layer, not an active integrated runtime service.

For the whole-project academic argument, this is actually an important point:
the current Reva system has perception and prediction, but its central
decision-making agency remains incomplete. That missing layer is the main
research opportunity.

## 9. Agentic Interpretation of Existing Features

An intelligent agent is commonly characterized by situatedness, sociability,
autonomy, and adaptability. Reva already has partial support for each
characteristic.

### 9.1 Situatedness

Situatedness means the agent is embedded in, and responsive to, an environment.
For Reva, the environment is the Sri Lankan real estate market plus the user's
personal property context.

| Existing Feature | How It Supports Situatedness |
| --- | --- |
| User portfolio database | Gives Reva awareness of the user's owned properties and investment exposure. |
| Property type-specific records | Allows separate reasoning over land, housing, and rentals. |
| Land model geocoding and distance features | Gives the system spatial context. |
| Market sentiment pipeline | Gives the system awareness of market news and public/economic mood. |
| Sentiment cache | Allows the backend to access current market state. |
| Prediction models | Provide state estimates about property value. |
| Map explorer | Introduces geographic interaction, although currently simulated. |
| Portfolio dashboard | Shows the user's current financial situation and property mix. |

Current maturity: medium. Reva perceives several useful signals, but current
portfolio valuation and map exploration are still incomplete.

### 9.2 Sociability

Sociability means the agent can communicate and cooperate with humans or other
systems.

| Existing Feature | How It Supports Sociability |
| --- | --- |
| Ask Reva chatbot | Provides natural-language communication. |
| Prediction form cards inside chat | Combines conversation with structured data collection. |
| Dashboard insights | Communicates portfolio status in user-friendly language. |
| Admin interface | Lets human administrators govern model features and deployments. |
| Auth/profile system | Supports persistent user identity. |
| Support and home pages | Explain system purpose and expected workflows. |
| Frontend visualizations | Present outputs through charts, cards, tables, and maps. |

Current maturity: medium-high. Reva is socially accessible, but dialogue memory,
tool-grounded responses, and personalized conversation remain limited.

### 9.3 Autonomy

Autonomy means the agent can take goal-directed actions without direct manual
instruction for every step.

| Existing Feature | How It Supports Autonomy |
| --- | --- |
| Scheduler | Can periodically update sentiment cache and run sentiment pipelines. |
| Active model registry | Lets the system route predictions to the current approved model. |
| Dynamic prediction endpoint | Performs validation, model resolution, invocation, and record storage. |
| Portfolio insights | Automatically summarizes user portfolio state. |
| Planned RL layer | Intended to choose buy/hold/sell actions. |
| Chatbot trigger logic | Automatically maps certain natural-language intents to UI actions. |

Current maturity: low-medium. Reva automates some operations, but it does not
yet perform robust autonomous planning, monitoring, alerting, or investment
decision execution.

### 9.4 Adaptability

Adaptability means the agent can improve or adjust behavior as conditions,
models, users, or data change.

| Existing Feature | How It Supports Adaptability |
| --- | --- |
| Dynamic feature definitions | Prediction forms can evolve without hardcoding every field. |
| Model registry and activation | Model versions can be changed without rewriting the application. |
| Prediction history | Provides a basis for auditing and future learning. |
| User preferences | Captures risk level, preferred property type, and investment horizon. |
| Sentiment recency weighting | Allows market signals to change over time. |
| Rental service readiness check | Supports staged model rollout. |

Current maturity: medium. The system is architecturally adaptable, but it does
not yet learn from user feedback, prediction errors, or investment outcomes.

## 10. Proposed Agentic Architecture

The proposed research architecture is a central Reva Agent Orchestrator that
coordinates the existing services as tools.

### 10.1 Agent Modules

| Module | Responsibility |
| --- | --- |
| Perception module | Collect user state, portfolio, market prices, model outputs, sentiment, and conversation context. |
| Memory module | Store user profile, preferences, properties, prediction history, conversation history, and recommendation history. |
| Intent module | Interpret user requests from chat or UI actions. |
| Tool planner | Select which services to call: valuation, sentiment, portfolio, map, recommendation, or explanation. |
| Forecast module | Query land, house, and rental models. |
| Decision module | Generate investment recommendations using rules, RL, or risk-aware decision policies. |
| Explanation module | Translate technical outputs into user-facing advice. |
| Monitoring module | Periodically check market/sentiment/portfolio changes and trigger alerts. |
| Governance module | Enforce model registry, permissions, audit logs, and human-in-the-loop controls. |

### 10.2 Agent Tool Set

The existing system can be reframed as a tool-using agent:

| Tool | Existing Source |
| --- | --- |
| `predict_land_price` | Land model service and dynamic prediction endpoint |
| `predict_house_price` | House model service and dynamic prediction endpoint |
| `predict_rental_price` | Rental service scaffold |
| `get_portfolio_summary` | Portfolio backend service |
| `get_property_records` | Portfolio/property backend |
| `get_market_sentiment` | Sentiment cache and sentiment pipeline |
| `get_active_model` | Admin model registry |
| `validate_prediction_features` | Dynamic feature service |
| `recommend_investment_action` | Planned RL/recommendation layer |
| `explain_recommendation` | Proposed explanation module |
| `store_prediction_event` | Prediction record table |
| `store_conversation_event` | Proposed memory extension |

### 10.3 Target Control Loop

```text
1. Observe:
   User request, portfolio state, preferences, market sentiment, model registry.

2. Interpret:
   Classify intent: valuation, portfolio analysis, recommendation, explanation,
   comparison, monitoring, or general real estate question.

3. Plan:
   Select tools and decide required data.

4. Act:
   Call prediction models, sentiment services, portfolio services, and
   recommendation policy.

5. Explain:
   Return advice with reasons, uncertainty, risks, and next steps.

6. Remember:
   Store prediction, recommendation, user feedback, and conversation summary.

7. Adapt:
   Update future recommendations based on user preferences, outcomes, and
   market changes.
```

This loop would transform Reva from an intelligent application into an
agentic advisory system.

## 11. Critical Research Gap

The core research gap is:

> Existing real estate technology systems usually provide isolated predictions
> or listing search, while Reva aims to become a personalized, situated,
> sentiment-aware, multi-model, agentic advisor for real estate investment
> decisions.

The current system has many components, but lacks a formal agent architecture
that integrates them into goal-directed behavior. The missing research problem
is not only model accuracy. It is how to coordinate prediction, sentiment,
portfolio memory, user preferences, risk constraints, and recommendations into
a single trustworthy agent.

## 12. Proposed Research Problem Statement

This research investigates how a modular real estate prediction platform can be
transformed into an agentic advisory architecture that exhibits situatedness,
sociability, autonomy, and adaptability while supporting personalized property
valuation, portfolio monitoring, market sentiment analysis, and investment
recommendation.

## 13. Research Questions

RQ1: How can price prediction models, market sentiment analysis, portfolio
memory, and RL-based decision support be integrated into a unified real estate
agent architecture?

RQ2: To what extent do the current Reva features satisfy the agentic
characteristics of situatedness, sociability, autonomy, and adaptability?

RQ3: How can a conversational interface such as Ask Reva be transformed from a
prompt-trigger chatbot into a tool-grounded real estate advisory agent?

RQ4: How can user preferences, portfolio state, and market uncertainty improve
the personalization and safety of real estate recommendations?

RQ5: How can model governance, active model selection, and prediction history
support adaptive and accountable agent behavior?

## 14. Proposed Novelty

The proposed novelty is not just another house-price predictor. It is:

> An agentic real estate advisory architecture that combines modular property
> price models, market sentiment perception, user portfolio memory, dynamic
> model governance, and RL-style investment decision support into a personalized
> real estate agent.

Potential contributions:

1. A domain-specific agentic architecture for real estate advisory.

2. A classification of real estate platform features under the agentic
   dimensions of situatedness, sociability, autonomy, and adaptability.

3. A tool-grounded chatbot architecture for real estate prediction and
   investment advice.

4. A model governance framework where an agent selects only active,
   admin-approved model endpoints.

5. A future RL decision layer that recommends buy/hold/sell actions using
   personal portfolio state and market sentiment.

## 15. Recommended System Evolution

### Phase 1: Make Existing Services Reliable

1. Connect portfolio current value to active model services or a proper market
   valuation function.

2. Complete the rental model using the same pattern as the house service.

3. Mount or rebuild the recommendation API if RL recommendations are part of
   the production flow.

4. Replace chatbot-generated valuation results with actual calls to prediction
   endpoints.

5. Persist chat history and user feedback.

6. Fix authentication consistency between Google login and backend JWT
   validation.

### Phase 2: Introduce Agent Orchestration

1. Add an agent controller behind `/ask`.

2. Implement structured intent extraction.

3. Implement typed tool calls instead of marker strings.

4. Add conversation memory and recommendation memory.

5. Add an explanation generator grounded in tool outputs.

6. Add safety rules: uncertainty disclosure, affordability checks, and
   professional-advice disclaimers.

### Phase 3: Add Decision Intelligence

1. Develop risk-aware recommendation logic.

2. Integrate the RL decision policy with portfolio state and model forecasts.

3. Use user preferences such as risk level, property type, and investment
   horizon.

4. Add uncertainty-aware model outputs.

5. Add alerts for sentiment shocks and portfolio risk changes.

### Phase 4: Add Adaptation and Evaluation

1. Compare predictions against actual later market prices.

2. Learn from user feedback and decision outcomes.

3. Track model drift and sentiment drift.

4. Evaluate the agent using task success, recommendation usefulness, prediction
   accuracy, user trust, and safety metrics.

## 16. Evaluation Framework

### 16.1 Component Evaluation

| Component | Evaluation Metrics |
| --- | --- |
| Land model | MAE, RMSE, MAPE, R2, district-level error |
| House model | MAE, RMSE, MAPE, R2, location-level error |
| Rental model | MAE, RMSE, MAPE, occupancy/demand sensitivity |
| Sentiment model | Classification quality, relevance filtering accuracy, temporal stability |
| Portfolio valuation | Error against actual current market values |
| Chatbot | Intent accuracy, tool-call correctness, response groundedness |
| Recommendation policy | Return, risk-adjusted return, drawdown, feasibility, user preference alignment |
| Agent as a whole | Task completion, user satisfaction, trust, explanation quality, safety |

### 16.2 Agentic Evaluation

| Agentic Property | Evaluation Question |
| --- | --- |
| Situatedness | Does Reva use current user, market, location, and sentiment context? |
| Sociability | Can users communicate goals naturally and receive understandable advice? |
| Autonomy | Can Reva monitor, plan, recommend, and alert without manual step-by-step control? |
| Adaptability | Can Reva update behavior as users, models, data, and markets change? |

## 17. Academic Positioning

Reva sits at the intersection of:

- Real estate price prediction.
- Conversational AI.
- Sentiment analysis.
- Decision support systems.
- Reinforcement learning.
- Human-centered AI.
- Agentic software architecture.

The academic strength of the project is that it combines these areas in a
practical domain where decisions are expensive, personal, and highly dependent
on context. This makes Reva more interesting than a generic chatbot or a
single-property valuation model.

## 18. Current System Maturity Assessment

| Capability | Current Maturity | Evidence |
| --- | --- | --- |
| Public prediction UI | Medium-high | Land, house, rental pages exist and call dynamic backend endpoints. |
| Land prediction | High relative to project | Dedicated service, model artifact, feature engineering, time calibration. |
| House prediction | Medium-high | Dedicated service with CatBoost artifact and validation. |
| Rental prediction | Low | Service scaffold exists, model artifact is empty. |
| User portfolio tracking | Medium | Database, add-property modal, dashboard, summary APIs. |
| Current portfolio valuation | Low | Current price function is placeholder. |
| Sentiment analysis | Medium | Rich pipeline exists, but relevance/time-window issues need correction. |
| Chatbot | Medium | Good UI and Gemini integration, but not robustly tool-grounded. |
| Admin model governance | Medium-high | Feature and model management exist. |
| RL recommendation | Research-stage | Design exists, active runtime integration not present in inspected source snapshot. |
| Agentic orchestration | Low | Components exist, central agent loop does not. |

## 19. Conclusion

Reva already contains many foundations of a real-world real estate agent:
property memory, user profiles, valuation models, market sentiment perception,
portfolio summaries, a chatbot interface, and administrative model governance.
These components can be clearly mapped onto agentic characteristics:

- Situatedness through property data, market signals, model predictions, and
  sentiment.
- Sociability through chatbot interaction, dashboards, forms, and admin/user
  interfaces.
- Autonomy through scheduled updates, active model routing, automated
  prediction records, and planned recommendations.
- Adaptability through dynamic feature definitions, model registry, prediction
  history, and user preferences.

The main gap is orchestration. Reva is not yet a single agent that observes,
plans, acts, explains, remembers, and adapts. It is currently a modular
intelligent platform with the right ingredients for an agentic system.

The recommended academic direction is to present Reva as an emerging agentic
real estate advisory architecture and propose the next layer: a tool-grounded
Reva Agent Orchestrator that coordinates prediction models, sentiment analysis,
portfolio memory, user preferences, and RL-based recommendation into a coherent
agent capable of personalized real estate advice.

## 20. Suggested Report Title for Academic Submission

Designing an Agentic Real Estate Advisory System: A Modular Architecture for
Prediction, Sentiment-Aware Portfolio Monitoring, and Personalized Investment
Recommendation in Reva

