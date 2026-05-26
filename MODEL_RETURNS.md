# RL Agent
- Property Signals (no arguments)
{
  "land_trend": -0.1,
  "rental_yield": 0.007718515037593985,
  "housing_signal": -0.15
}
- get sentiment features (no arguments)
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
- Reccomendation (no args)
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

# Sentiment (no args)
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
- current prices
{
  "sales": {
    "national average": 85120000,
    "colombo": 65430000,
    "kalutara": 65430000,
    "galle": 49910000,
    "matara": 49910000,
    "hambantota": 49910000,
    "kandy": 85120000,
    "matale": 85120000,
    "nuwara eliya": 85120000,
    "kurunegala": 39180000,
    "puttalam": 39180000,
    "badulla": 85120000,
    "monaragala": 85120000,
    "ratnapura": 85120000,
    "kegalle": 85120000,
    "batticaloa": 85120000,
    "ampara": 85120000,
    "trincomalee": 85120000,
    "jaffna": 85120000,
    "mullaitivu": 85120000,
    "vavuniya": 85120000,
    "mannar": 85120000,
    "kilinochchi": 85120000,
    "gampaha": 85120000,
    "anuradhapura": 85120000,
    "polonnaruwa": 85120000
  },
  "rentals": {
    "colombo": 657000,
    "kalutara": 657000,
    "galle": 657000,
    "matara": 657000,
    "hambantota": 657000,
    "kandy": 657000,
    "matale": 657000,
    "nuwara eliya": 657000,
    "kurunegala": 657000,
    "puttalam": 657000,
    "badulla": 657000,
    "monaragala": 657000,
    "ratnapura": 657000,
    "kegalle": 657000,
    "batticaloa": 657000,
    "ampara": 657000,
    "trincomalee": 657000,
    "jaffna": 657000,
    "mullaitivu": 657000,
    "vavuniya": 657000,
    "mannar": 657000,
    "kilinochchi": 657000,
    "gampaha": 657000,
    "national average": 657000,
    "anuradhapura": 657000,
    "polonnaruwa": 657000
  },
  "lands": {
    "colombo": 16080000,
    "kalutara": 16080000,
    "galle": 821000,
    "matara": 821000,
    "hambantota": 821000,
    "kandy": 1530000,
    "matale": 1530000,
    "nuwara eliya": 1530000,
    "kurunegala": 628000,
    "puttalam": 628000,
    "badulla": 380000,
    "monaragala": 380000,
    "ratnapura": 215000,
    "kegalle": 215000,
    "batticaloa": 649000,
    "ampara": 649000,
    "trincomalee": 649000,
    "jaffna": 4390000,
    "mullaitivu": 4390000,
    "vavuniya": 4390000,
    "mannar": 4390000,
    "kilinochchi": 4390000,
    "gampaha": 4390000,
    "national average": 4390000,
    "anuradhapura": 4390000,
    "polonnaruwa": 4390000
  }
}

- cached return (no args)
{
  "land": {
    "next_close": "1,987,695.38",
    "next_5_close": [
      "1,987,695.38",
      "1,978,658.00",
      "1,970,954.12",
      "1,964,230.38",
      "1,958,224.88"
    ]
  },
  "housing": {
    "next_close": "4,889,387.00",
    "next_5_close": [
      "4,889,387.00",
      "5,062,534.50",
      "5,190,037.50",
      "5,341,720.50",
      "5,497,282.00"
    ]
  },
  "rental": {
    "next_close": "93,863,536.00",
    "next_5_close": [
      "93,863,536.00",
      "93,751,224.00",
      "93,574,280.00",
      "93,355,744.00",
      "93,111,648.00"
    ]
  },
  "updated_at": "2026-04-06T04:20:01.290055Z"
}
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
- Next sequence (arg:n = 5)
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