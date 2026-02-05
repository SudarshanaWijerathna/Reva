# System Architecture – Reva

## 1. Overview

Reva is an AI-powered Real Estate Virtual Assistant designed to provide
price predictions, market sentiment insights, and investment recommendations
for housing, rental, and land properties.

The system follows a **modular, layered architecture** where each AI component
is independently developed, evaluated, and integrated into a unified web
platform.

---

## 2. High-Level Architecture

The system is divided into five major layers:

1. Data Layer  
2. Machine Learning Layer  
3. Sentiment Analysis Layer  
4. Reinforcement Learning (Decision) Layer  
5. Web Platform Layer  

Each layer has a clear responsibility and minimal coupling with others.

---

## 3. Architecture Diagram (Conceptual)

```text
                 ┌──────────────────────────┐
                 │   External Text Sources  │
                 │ (News, Blogs, Reports)   │
                 └─────────────┬────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Sentiment Model     │
                    │  (NLP / LLM / VADER) │
                    └──────────┬──────────┘
                               │
                 Sentiment Signals (Score, Label)
                               │
   ┌───────────────────────────┼───────────────────────────┐
   │                           │                           │
┌──▼──────────┐        ┌───────▼────────┐         ┌────────▼───────┐
│ Land Price  │        │ House Price    │         │ Rental Price   │
│ Model       │        │ Model           │         │ Model           │
│ (Regression)│        │ (Regression)    │         │ (Regression)    │
└─────┬───────┘        └───────┬────────┘         └────────┬───────┘
      │                        │                           │
      └───────────────┬────────┴───────────┬───────────────┘
                      │                    │
              Predicted Prices & Trends
                      │
             ┌────────▼────────┐
             │ RL Agent         │
             │ (Buy/Hold/Sell)  │
             └────────┬────────┘
                      │
              Investment Recommendation
                      │
             ┌────────▼────────┐
             │ Web Platform     │
             │ (Public + Auth)  │
             └─────────────────┘
