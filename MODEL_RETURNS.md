# RL Agent
- Property Signals
{
  "land_trend": -0.1,
  "rental_yield": 0.007718515037593985,
  "housing_signal": -0.15
}
- get sentiment features
{
  "land": {
    "sentiment_current": -0.0832,
    "sentiment_trend": -0.05,
    "sentiment_volatility": 0.11920984299405256,
    "sentiment_shock": 0
  },
  "housing": {
    "sentiment_current": 0.0791,
    "sentiment_trend": 0.05,
    "sentiment_volatility": 0.1463714680758059,
    "sentiment_shock": 0
  },
  "rental": {
    "sentiment_current": -0.083,
    "sentiment_trend": -0.05,
    "sentiment_volatility": 0.08260049771171007,
    "sentiment_shock": 0
  }
}
- Reccomendation
{
  "action_index": 21,
  "action_vector": [
    2,
    1,
    0
  ],
  "action_labels": [
    "BUY",
    "HOLD",
    "SELL"
  ],
  "state_vector": [
    0,
    -0.0832,
    -0.05,
    0.11920984299405256,
    0,
    -0.1,
    0.007718515037593985,
    -0.15,
    1,
    -0.083,
    -0.05,
    0.08260049771171007,
    0,
    -0.1,
    0.007718515037593985,
    -0.15,
    1,
    0.0791,
    0.05,
    0.1463714680758059,
    0,
    -0.1,
    0.007718515037593985,
    -0.15,
    1
  ]
}

# Sentiment
{
  "overall": "neutral",
  "details": {
    "land": {
      "short_term": {
        "value": 0,
        "label": "neutral"
      },
      "medium_term": {
        "value": -0.0832,
        "label": "neutral"
      },
      "long_term": {
        "value": -0.284,
        "label": "bearish"
      }
    },
    "housing": {
      "short_term": {
        "value": 0,
        "label": "neutral"
      },
      "medium_term": {
        "value": 0.0791,
        "label": "neutral"
      },
      "long_term": {
        "value": 0.3424,
        "label": "bullish"
      }
    },
    "rental": {
      "short_term": {
        "value": 0,
        "label": "neutral"
      },
      "medium_term": {
        "value": -0.083,
        "label": "neutral"
      },
      "long_term": {
        "value": -0.2013,
        "label": "bearish"
      }
    }
  },
  "source": "cache_or_live"
}

# LSTM
- Next close
{
  "land": {
    "next_close": "1,987,695.38"
  },
  "housing": {
    "next_close": "4,889,387.00"
  },
  "rental": {
    "next_close": "93,863,536.00"
  }
}
- Next sequence (n = 5)
{
  "steps": 5,
  "land": {
    "sequence": [
      "1,987,695.38",
      "1,978,658.00",
      "1,970,954.12",
      "1,964,230.38",
      "1,958,224.88"
    ]
  },
  "housing": {
    "sequence": [
      "4,889,387.00",
      "5,062,534.50",
      "5,190,037.50",
      "5,341,720.50",
      "5,497,282.00"
    ]
  },
  "rental": {
    "sequence": [
      "93,863,536.00",
      "93,751,224.00",
      "93,574,280.00",
      "93,355,744.00",
      "93,111,648.00"
    ]
  }
}