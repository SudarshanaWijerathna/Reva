from statsmodels.tsa.arima.model import ARIMAResults
from scipy.special import inv_boxcox
from pathlib import Path
import json

# resolve paths relative to this file so execution cwd does not matter
base_dir = Path(__file__).resolve().parent

# load model
model = ARIMAResults.load(base_dir / "arima_boxcox_model.pkl")

# load lambda
with open(base_dir / "metadata.json") as f:
    lam = json.load(f)["lambda"]

# forecast
steps = 12
boxcox_forecast = model.forecast(steps=steps)

# inverse transform
forecast = inv_boxcox(boxcox_forecast, lam)

print(forecast)
