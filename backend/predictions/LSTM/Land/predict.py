import numpy as np
import pandas as pd
from pathlib import Path
from importlib import import_module
import joblib
from backend.predictions.LSTM.Land.thresholds import time_steps
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "LandDF.csv"
MODEL_PATH = Path(__file__).resolve().parent / "my_model.keras"
SCALER_PATH = Path(__file__).resolve().parent / "scaler.joblib"


def _load_land_df(csv_path=None):
    path = Path(csv_path) if csv_path else DATASET_PATH
    return pd.read_csv(path)


def _load_keras_model(model_file):
    try:
        keras_models = import_module("tensorflow.keras.models")
    except ModuleNotFoundError:
        keras_models = import_module("keras.models")
    return keras_models.load_model(model_file)


def _format_prediction_value(value, decimals=2):
    return f"{float(value):,.{decimals}f}"


def load_land_model_and_scaler(model_path=None, scaler_path=None):
    model_file = Path(model_path) if model_path else MODEL_PATH
    scaler_file = Path(scaler_path) if scaler_path else SCALER_PATH

    model = _load_keras_model(model_file)
    scaler = joblib.load(scaler_file)

    return model, scaler


def predict_next_close_price(model, scaler, df=None, csv_path=None):
    if df is None:
        df = _load_land_df(csv_path)

    if "close" not in df.columns:
        raise ValueError("CSV/DataFrame must contain a 'close' column")

    if len(df) < time_steps:
        raise ValueError(f"Need at least {time_steps} rows, found {len(df)}")

    # Use the most recent time_steps close prices
    last_60_days = df["close"].tail(time_steps).to_numpy().reshape(-1, 1)

    # scale
    last_60_scaled = scaler.transform(last_60_days)

    # reshape for LSTM
    X_input = last_60_scaled.reshape(1, time_steps, 1)

    # predict
    pred = model.predict(X_input, verbose=0)

    # inverse scale
    pred_actual = scaler.inverse_transform(pred)

    predicted_close = float(pred_actual[0][0])
    print("Predicted next close:", _format_prediction_value(predicted_close))
    return predicted_close


def predict_next_close_price_from_saved(csv_path=None, model_path=None, scaler_path=None):
    model, scaler = load_land_model_and_scaler(model_path=model_path, scaler_path=scaler_path)
    return predict_next_close_price(model=model, scaler=scaler, df=None, csv_path=csv_path)

def predict_future_sequence(model, scaler, df=None, csv_path=None, steps=10):

    if df is None:
        df = _load_land_df(csv_path)

    last_60_days = df["close"].tail(time_steps).to_numpy()
    last_60_scaled = scaler.transform(last_60_days.reshape(-1, 1))

    predictions = []

    # Initialize current_sequence with the scaled historical data
    current_sequence = last_60_scaled

    for _ in range(steps):
        # reshape for model
        X_input = current_sequence.reshape(1, time_steps, 1)

        # predict next step
        pred = model.predict(X_input, verbose=0)

        # store prediction
        predictions.append(pred[0][0])

        # append prediction & remove oldest value
        current_sequence = np.vstack((current_sequence[1:], pred))

    # inverse scale
    predictions = np.array(predictions).reshape(-1, 1)
    predictions = scaler.inverse_transform(predictions)
    formatted_predictions = [_format_prediction_value(v[0]) for v in predictions]
    print(f"Predicted next {steps} close prices:", formatted_predictions)

    return predictions

def predict_future_sequence_from_saved(csv_path=None, model_path=None, scaler_path=None, steps=10):
    model, scaler = load_land_model_and_scaler(model_path=model_path, scaler_path=scaler_path)
    return predict_future_sequence(model=model, scaler=scaler, df=None, csv_path=csv_path, steps=steps)

if __name__ == "__main__":
    predict_next_close_price_from_saved()
    predict_future_sequence_from_saved(steps=5)
    