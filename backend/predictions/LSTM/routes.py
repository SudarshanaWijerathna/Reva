from fastapi import APIRouter, HTTPException, status
from backend.auth.routes import user_dependency, Database
from backend.predictions.LSTM.Land.predict import (
	predict_next_close_price_from_saved as predict_land_next_close,
	predict_future_sequence_from_saved as predict_land_sequence,
)
from backend.predictions.LSTM.Housing.predict import (
	predict_next_close_price_from_saved as predict_housing_next_close,
	predict_future_sequence_from_saved as predict_housing_sequence,
)
from backend.predictions.LSTM.Rental.predict import (
	predict_next_close_price_from_saved as predict_rental_next_close,
	predict_future_sequence_from_saved as predict_rental_sequence,
)
from backend.core.cache_service import get_future_predictions,get_current_prices
router = APIRouter(
	prefix="/api/lstm",
	tags=["LSTM Predictions"],
)


@router.get("/next-close")
def get_next_close_prices(
	user: user_dependency,
    db: Database,
):
	return {
		"land": {"next_close": predict_land_next_close()},
		"housing": {"next_close": predict_housing_next_close()},
		"rental": {"next_close": predict_rental_next_close()},
	}


@router.get("/future-sequence")
def get_future_sequences(
	user: user_dependency,
    db: Database,
	steps: int = 5
):
	if steps < 1:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="steps must be a positive integer",
		)

	return {
		"steps": steps,
		"land": {"sequence": predict_land_sequence(steps=steps)},
		"housing": {"sequence": predict_housing_sequence(steps=steps)},
		"rental": {"sequence": predict_rental_sequence(steps=steps)},
	}
