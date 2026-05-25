# Local ML Model Services

Reva is designed so the web backend calls each ML model through a small HTTP
service. That is the same shape you can use locally and in Azure.

## Ports

Use these local ports to avoid colliding with the backend and frontend:

| Model | Local URL | Predict endpoint |
| --- | --- | --- |
| Land | `http://127.0.0.1:8011` | `http://127.0.0.1:8011/predict` |
| House | `http://127.0.0.1:8012` | `http://127.0.0.1:8012/predict` |
| Rental | `http://127.0.0.1:8013` | `http://127.0.0.1:8013/predict` |

## Start One Service

Install the shared local runtime dependencies first:

```powershell
backend\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
```

From the repository root:

```powershell
.\scripts\run_model_service.ps1 -Model land
.\scripts\run_model_service.ps1 -Model house
.\scripts\run_model_service.ps1 -Model rental
```

Or run the underlying command directly:

```powershell
backend\.venv\Scripts\python.exe -B -m uvicorn ml.land_service.app:app --host 127.0.0.1 --port 8011 --reload
backend\.venv\Scripts\python.exe -B -m uvicorn ml.house_service.app:app --host 127.0.0.1 --port 8012 --reload
backend\.venv\Scripts\python.exe -B -m uvicorn ml.rental_service.app:app --host 127.0.0.1 --port 8013 --reload
```

Each service has a health endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8011/health
Invoke-RestMethod http://127.0.0.1:8012/health
Invoke-RestMethod http://127.0.0.1:8013/health
```

## Point The Backend At Local Services

Before starting the backend, set the model service URLs in the same terminal:

```powershell
$env:LAND_MODEL_API_URL = "http://127.0.0.1:8011/predict"
$env:HOUSE_MODEL_API_URL = "http://127.0.0.1:8012/predict"
$env:RENTAL_MODEL_API_URL = "http://127.0.0.1:8013/predict"

backend\.venv\Scripts\python.exe -B -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

Environment variables override the admin model registry, which is useful for
local development. If an env var is not set, the backend falls back to the
active endpoint in the admin model registry.

## Test A Service Directly

House:

```powershell
$body = @{
  features = @{
    house_sqft = 1800
    land_sqft = 2722.5
    bedrooms = 3
    bathrooms = 2
    lat = 6.9271
    lon = 79.8612
    district = "Colombo"
    sub_location = "Colombo"
    posted_year = 2025
    posted_month = 12
    description = "Semi luxury house. 20 ft carpet road. Water and electricity. 1 km to town."
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post http://127.0.0.1:8012/predict -ContentType "application/json" -Body $body
```

Land:

```powershell
$body = @{
  features = @{
    land_size = 20
    district = "Colombo"
    location_text = "Maharagama"
    main_road = $true
    electricity = $true
    clear_deed = $true
    water = $true
    bank_loan = $true
    near_town = $true
    distance_to_town_m = 500
    period = "2025 H2"
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post http://127.0.0.1:8011/predict -ContentType "application/json" -Body $body
```

## Azure Shape

Deploy each folder as its own service/container:

```text
ml/land_service   -> https://<land-service>/predict
ml/house_service  -> https://<house-service>/predict
ml/rental_service -> https://<rental-service>/predict
backend           -> calls the three service endpoints
frontend          -> calls backend only
```

In Azure, set these backend app settings:

```text
LAND_MODEL_API_URL=https://<land-service>/predict
HOUSE_MODEL_API_URL=https://<house-service>/predict
RENTAL_MODEL_API_URL=https://<rental-service>/predict
```

Alternatively, leave the env vars empty and register those URLs through the
admin model registry as active model endpoints.
