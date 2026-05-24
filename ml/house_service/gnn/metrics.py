from typing import Dict

import numpy as np


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    error = y_pred - y_true
    absolute_error = np.abs(error)
    percentage_error = absolute_error / np.maximum(np.abs(y_true), 1.0)
    return {
        "mae": float(np.mean(absolute_error)),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mape": float(np.mean(percentage_error) * 100.0),
        "median_ape": float(np.median(percentage_error) * 100.0),
    }


def imputation_metrics(numeric_true: np.ndarray, numeric_pred: np.ndarray) -> Dict[str, float]:
    numeric_true = np.asarray(numeric_true, dtype=float)
    numeric_pred = np.asarray(numeric_pred, dtype=float)
    error = numeric_pred - numeric_true
    return {
        "numeric_mae": float(np.mean(np.abs(error))),
        "numeric_rmse": float(np.sqrt(np.mean(error**2))),
    }


def final_price_per_sqft(base_price_per_sqft: np.ndarray, residual_log_price: np.ndarray) -> np.ndarray:
    base_log = np.log1p(np.maximum(np.asarray(base_price_per_sqft, dtype=float), 1.0))
    return np.maximum(np.expm1(base_log + np.asarray(residual_log_price, dtype=float)), 1.0)
