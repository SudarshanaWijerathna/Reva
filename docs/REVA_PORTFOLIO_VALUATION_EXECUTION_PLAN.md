# REVA Portfolio Current Value and Return Plan

**Research date:** 2026-08-09  
**Scope:** `backend/portfolio`, property storage, ML valuation services, market indices, portfolio API, and dashboard

## Implementation status (2026-08-09)

The production foundation in phases 1-7 is implemented:

- additive property, valuation-snapshot, and transaction-ledger schema
- canonical land, house, rental, and rental-underlying-house payload builders
- version/hash provenance for model artifacts, feature inputs, and observed index
- property AVM anchor multiplied only by a matched observed index ratio
- Colombo-only CBSL adjustment with `anchor_only` outside supported geography
- rental market-rent/NOI/capital-value separation and market/income reconciliation
- cost basis, unrealized gain, rental cash flow, total return, and sold-property accounting
- quarterly snapshot scheduler and snapshot/transaction API routes
- dashboard labels, as-of/status/confidence/range evidence, and expanded property forms
- frozen LSTM training data separated from newly published observed-index rows
- forecast index disabled by default because it does not beat the naive benchmark

Phases 8-9 are operational gates, not one-time code tasks. V2 must still run through
an index-refresh shadow cycle, be compared with later observed listings/sales, and
meet the backtest/coverage thresholds below before being described as a production-
grade appraisal. Retraining remains a six-month evaluation cadence, not automatic
promotion.

## 1. Decision

REVA should define a property's **current value** as:

> The estimated market value of the specific property, in LKR, as of a stated valuation date.

The production formula should be:

```text
anchor_value(property, model_version)
    x observed_index(segment, geography, valuation_date)
      / observed_index(segment, geography, model_anchor_date)
    = estimated_current_value
```

This is a sound architecture, with four constraints:

1. The anchor must be a property-specific total value from the appropriate ML model.
2. The index must measure the same asset segment and a defensible geography.
3. A current value may use observed index data only. Forecasts must be separate.
4. Every result must expose its valuation date, model/index versions, confidence, range, and fallback reason.

The dashboard's current `profit` field should be renamed **unrealized capital gain**. A separate **total return** should include net rental cash flow and costs.

## 2. Why the current implementation is not yet defensible

### 2.1 It mixes three different valuation methods

`backend/portfolio/valuation.py` currently does the following in `hybrid` mode:

| Asset | Current path | Problem |
|---|---|---|
| Land | Land ML total value x market-index factor | Closest to the target design, but the portfolio payload invents several missing features and can misuse location as district. |
| Housing | House ML only if bedrooms and bathrooms exist; otherwise scraper average | The database does not store bedrooms or bathrooms, so existing housing records always fall back. |
| Rental investment | Stored gross monthly rent capitalised using one national yield | It does not use the rental ML model, does not deduct vacancy/expenses, and does not reconcile against a sale-value model. |

The table therefore displays values produced by different methods while describing all of them as ML valuations.

### 2.2 The index is stale and geographically narrow

The local market-index dataset ends at `2025-03`, while the current date is August 2026. CBSL has already published monthly asking-price observations through `2026-03`: land `176.9`, houses `187.0`, and condominiums `208.2` (2019=100). REVA is therefore one full year behind the latest official observation even before any forecast is considered. The CBSL asking-price indices represented in the repository cover Colombo district. Applying them silently to Gampaha, Kalutara, or an unknown locality would overstate precision.

The current `market_index.growth_factor()` correctly degrades to `1.0` when the target is too far past the series. As a result, a value shown as current may actually remain at its model anchor date.

### 2.3 The LSTM is not suitable for current valuation

The repository's `ml/market_index_training_report.json` shows that the naive forecast beats the LSTM for both houses and land at 1-, 3-, and 6-month horizons. The LSTM therefore fails the minimum benchmark for use in valuation.

Even after a future model beats that benchmark, predicted index points are forecasts, not observed market conditions. They may power a separately labeled forecast but must not silently enter `estimated_current_value`.

### 2.4 The portfolio schema cannot reproduce prediction-screen inputs

The prediction services accept materially richer property descriptions than the portfolio tables store. Examples include:

- Housing: bedrooms, bathrooms, coordinates, sub-location, parking, road width, utilities, condition/quality, and description-derived amenities.
- Rental: property type, bedrooms, bathrooms, floor area, furnishing, parking, lease terms, and amenities.
- Land: a real district separate from locality, utilities, deed/loan eligibility, proximity, and explicit road details.

Unless the portfolio stores the same canonical features, the dashboard cannot be expected to match a prediction made with a complete form.

### 2.5 `profit` is underspecified

The current formula is:

```text
current_value - purchase_price
```

That is an **unrealized capital gain**, not complete profit. It excludes acquisition costs, improvements, selling costs, rental income, vacancies, maintenance, taxes, insurance, financing, and any realized sale proceeds.

## 3. Research findings that govern the design

1. International Valuation Standards define market value at a specific valuation date. A value without an `as_of` date is incomplete.
2. The CBSL Asking Price Indices use hedonic rolling-window time-dummy methods, are based on advertisements, and cover Colombo district. They are useful trend indicators but are not nationwide transaction-price indices.
3. The CBSL Land Valuation Indicator is semi-annual, covers Colombo district, and is based on per-perch bare-land assessments from the Government Valuation Department. Residential, commercial, and industrial land are separate sub-indicators.
4. International property-index guidance recommends quality adjustment because simple averages change when the mix of properties changes. Hedonic and repeat-sales indices are standard solutions.
5. AVM guidance calls for independent holdouts, out-of-time testing, confidence measures, monitoring, and recalibration when holdout performance drifts.
6. For investment property, fair value reflects market conditions at the reporting date. A fair-value change is distinct from rental cash flow and disposal profit.

These findings support a property-level AVM for the price level, an observed and segment-matched index for temporal movement, and transparent uncertainty.

## 4. Product definitions

### 4.1 Estimated current value

```text
estimated_current_value(p, t)
    = anchor_market_value(p, a)
    x observed_index(s, g, t*) / observed_index(s, g, a)
```

Where:

- `p` is the property.
- `a` is the model's declared price anchor date.
- `t` is the requested valuation date.
- `t*` is the latest observed index date on or before `t`.
- `s` is the matching segment: residential land, house sale, condominium sale, or rent.
- `g` is the matching geography.

If the index does not cover both `a` and `t*`, REVA must not extrapolate and call the result current. It should return the anchor value with `status="stale"`, its actual `as_of` date, and reduced confidence.

### 4.2 Forecast value

```text
forecast_value(p, h)
    = estimated_current_value(p, latest_observed_date)
    x forecast_index(s, g, h) / observed_index(s, g, latest_observed_date)
```

This belongs in a forecast view and must include the horizon and a prediction interval. It must never replace current value in the properties table.

### 4.3 Acquisition cost basis

```text
cost_basis
    = purchase_price
    + acquisition_costs
    + capital_improvements
```

Acquisition costs can include legal, valuation, stamp, registration, and directly attributable purchase costs. Improvements should exclude routine repairs already treated as operating expenses.

### 4.4 Unrealized capital gain

```text
unrealized_capital_gain = estimated_current_value - cost_basis
unrealized_gain_pct     = unrealized_capital_gain / cost_basis x 100
```

This is the appropriate replacement for the current `profit` column while a property remains owned.

### 4.5 Net rental income and total return

```text
net_rental_income
    = rent_received
    - vacancy_loss
    - maintenance
    - management_fees
    - rates_and_taxes
    - insurance
    - other_operating_costs

total_return_lkr
    = unrealized_capital_gain
    + cumulative_net_rental_income
```

Financing return should be an optional, separate leveraged view because interest and principal affect cash return differently.

### 4.6 Realized gain after sale

```text
realized_gain
    = sale_price
    - selling_costs
    - cost_basis
```

Once sold, freeze the last valuation and stop presenting an unrealized gain as current profit.

## 5. Valuation hierarchy by asset

### 5.1 Land

Primary method:

```text
land_model_price_per_perch
    x land_size_perches
    x observed_residential_land_index_ratio
```

Rules:

- Use the residential LVI/API segment for residential plots, not the aggregate LVI.
- Keep `district`, `locality`, and geocode as separate fields.
- Never default electricity, water, clear deed, distance, or loan eligibility to favorable values. Missing means unknown.
- Colombo index coverage may not be presented as high-confidence Gampaha/Kalutara movement.
- Return price per perch and total plot value together.

### 5.2 Owner-occupied house

Primary method:

```text
house_AVM_total_at_anchor x observed_house_index_ratio
```

Rules:

- Add the missing portfolio features so it can call the same house model as the prediction endpoint.
- Use the property's actual feature snapshot, not invented defaults.
- Keep land and building attributes in the model payload.
- If the property has been materially improved since purchase, update its feature snapshot and record the improvement separately in cost basis.

### 5.3 Rental investment property

The capital value of a rental property is not its monthly rent. Use two approaches when data permit:

1. **Market approach:** value the underlying house/apartment with the sale AVM and observed sale index.
2. **Income approach:** capitalise stabilised net operating income using a location/property-type cap rate derived from comparable sales and rents.

```text
NOI = effective_gross_rent - operating_expenses
income_value = annual_NOI / market_cap_rate
```

Reconcile the two estimates using evidence quality. Do not average blindly:

- Strong sale-model coverage + weak expense data: emphasize market approach.
- Strong lease/expense/cap-rate evidence: increase income-approach weight.
- Large disagreement: widen the interval and lower confidence.

The rental ML model estimates **monthly market rent**, not capital value. It should update the income side, not directly populate `current_value`.

## 6. Index policy

### 6.1 Current values

- Use published observations only.
- Store source, release/version, segment, geography, observation date, and ingestion date.
- Prefer transaction indices where available; asking-price indices must be labeled as such.
- Match geography and segment strictly.
- Snapshot portfolio valuations quarterly using the latest observation available at quarter end.
- Recompute past snapshots only when an index revision policy explicitly allows it; otherwise preserve the originally displayed value and store a revised series separately.

### 6.2 Forecasts

- The first benchmark is flat/naive; the second is drift.
- An LSTM may ship only when rolling-origin tests beat both benchmarks at the intended horizon.
- Disable the current LSTMs for user-visible forecasts until that gate is met.
- Forecasts must expose horizon, model date, interval, and `forecast` labeling.

### 6.3 Missing regional indices

For geography outside an official index's coverage:

1. Build REVA regional hedonic indices from deduplicated listings, segmented by asset and geography.
2. Benchmark them against CBSL where coverage overlaps.
3. Report asking-price provenance and confidence.
4. Until validation passes, use the property model's latest supported date and mark the current valuation stale rather than borrowing Colombo silently.

## 7. Model lifecycle

The proposed six-month retraining cadence is reasonable as a maximum interval, but drift—not the calendar alone—should trigger retraining.

### Every month or source release

- Ingest observed index data.
- Validate revisions, missing periods, jumps, and segment/geography metadata.
- Revalue only properties for which a valid newer observed factor exists.

### Every quarter

- Create immutable valuation snapshots for every active property.
- Run out-of-time performance and drift reports by asset, district, price band, and confidence tier.
- Compare the composite valuation against anchor-only and simple index-only baselines.

### Every six months

- Retrain each property-level model on a time-based split if sufficient new data exist.
- Promote only if the challenger passes all quality gates.
- Re-estimate uncertainty intervals and coverage tiers.
- Set the new model's anchor from its actual calibration period; do not assume the training end date.
- Do not reapply index growth already learned by the new model.

## 8. Required data-model changes

### Shared `properties`

Add:

- `district`, `locality`, `latitude`, `longitude`
- `acquisition_costs`, `capital_improvements`
- `sold_at`, `sale_price`, `selling_costs`
- `feature_snapshot_version`, `features_updated_at`

### Housing details

Add at minimum:

- `bedrooms`, `bathrooms`
- `parking_spaces`, `road_width_ft`
- utilities and major amenities used by the model
- optional description/condition fields used by feature extraction

### Rental investment details

Add:

- the same physical features needed to value the underlying property
- `actual_monthly_rent`, `market_monthly_rent`
- vacancy, maintenance, management, taxes/rates, insurance, and other operating expenses
- property subtype and furnishing status

### Valuation snapshots

Create a `property_valuation_snapshots` table containing:

- property and valuation IDs
- `estimated_value`, `lower_value`, `upper_value`, currency
- `valuation_as_of`, `computed_at`, status
- method and reconciliation weights
- model name/version/anchor
- index source/version/segment/geography/anchor/observation/factor
- feature snapshot or stable feature hash
- confidence and reason codes

### Portfolio transactions

Create a ledger for acquisition costs, improvements, rental income, operating expenses, and sale costs. Derived returns should come from this ledger instead of mutable totals.

## 9. API and UI contract

Return per property:

```json
{
  "estimated_current_value": 53500000,
  "valuation_as_of": "2026-06-30",
  "valuation_status": "observed_index",
  "value_range": {"lower": 45500000, "upper": 62500000, "coverage": "p80"},
  "confidence": "medium",
  "valuation_method": "house_avm_x_observed_house_index",
  "cost_basis": 32200000,
  "unrealized_capital_gain": 21300000,
  "unrealized_gain_pct": 66.15,
  "cumulative_net_rental_income": 0,
  "total_return_lkr": 21300000,
  "provenance": {
    "model_version": "...",
    "model_anchor": "2025-12",
    "index_source": "...",
    "index_observation": "2026-06",
    "index_factor": 1.034
  }
}
```

Dashboard changes:

- Rename `Current Val` to `Estimated value`.
- Show `As of <date>` beside the value.
- Rename `Profit` to `Unrealized gain`.
- Add a separate total-return view for rentals.
- Show a range, confidence badge, and method tooltip.
- Show `Stale` or `Anchor only` rather than implying a stale estimate is current.
- Do not strip valuation metadata in `frontend/src/services/portfolioService.ts`.

## 10. Validation and promotion gates

### Data splitting

- Use chronological train/validation/test splits.
- Keep an untouched out-of-time holdout.
- Deduplicate relisted properties across splits.
- Report by district, asset subtype, price decile, and data-completeness tier.

### Metrics

Track:

- MAE, RMSE, MAPE, median absolute percentage error
- median predicted-to-observed ratio
- coefficient of dispersion and price-related bias
- p80/p90 interval empirical coverage and width
- directional accuracy for index forecasts
- stale/fallback rate and coverage by method

### Initial promotion gates

1. Composite `AVM x observed index` must beat anchor-only and index-only baselines on the out-of-time holdout.
2. No major district or price band may degrade by more than 5% relative median error without an explicit low-confidence classification.
3. The observed coverage of a p80 interval should be approximately 75-85%.
4. Current-value coverage must be high enough that fallback/stale rows are visible and quantified, not hidden.
5. Forecast models must beat naive and drift at each horizon they claim to support.

These are release gates, not claims that every individual property is accurate to those percentages.

## 11. Execution plan

### Phase 0 — Freeze definitions and baseline

**Work**

- Approve the definitions in section 4.
- Snapshot current portfolio outputs and method metadata.
- Add contract tests around existing endpoints.
- Add a `PORTFOLIO_VALUATION_V2` feature flag.

**Acceptance**

- Existing behavior remains reproducible.
- Every baseline row identifies its current method and actual as-of date.

### Phase 1 — Complete the property and financial schema

**Work**

- Add the fields and tables in section 8 through migrations.
- Update create/edit forms and API schemas.
- Backfill what can be derived; mark the rest unknown.
- Never backfill favorable assumptions such as clear deed or utilities.

**Acceptance**

- A property saved from the portfolio can produce the same canonical model payload as the corresponding prediction form.

### Phase 2 — Version models, anchors, indices, and features

**Work**

- Add manifests for land, house, and rental models.
- Record training window, calibration/anchor date, target unit, supported geography, metrics, feature schema, and artifact hash.
- Version observed index series and provenance.
- Add a canonical payload builder shared by predictions and portfolio valuation.

**Acceptance**

- Replaying a valuation with the stored versions and feature snapshot returns the same result.

### Phase 3 — Build observed index ingestion

**Work**

- Update the CBSL series beyond March 2025 where official releases are available.
- Separate land, house, condominium, and rent segments.
- Build regional REVA asking-price indices only where official coverage is absent.
- Add data quality, staleness, revision, and geographic-eligibility checks.

**Acceptance**

- `observed_growth_factor()` never consumes forecast values and refuses invalid geography/segment combinations.

### Phase 4 — Implement a unified valuation service

**Target:** replace asset-specific shortcuts in `backend/portfolio/valuation.py`.

**Work**

- Implement `value_as_of(property, date)` with model and index adapters.
- Use the shared active-model runtime rather than direct imports.
- Return a typed result with value, range, confidence, method, status, provenance, and reasons.
- Add strict fallbacks: model anchor only, comparable market approach, or unavailable.

**Acceptance**

- Prediction endpoint and portfolio valuation match when given identical features, model version, anchor, and valuation date.

### Phase 5 — Implement asset methods and reconciliation

**Work**

- Land: total-value model plus matched observed residential-land factor.
- House: complete payload plus matched observed house factor.
- Rental: rental ML for market rent; house/sale AVM for capital value; NOI/cap-rate income method; evidence-weighted reconciliation.
- Propagate uncertainty from model and index rather than returning only a point estimate.

**Acceptance**

- Unit tests verify dimensions and units.
- Missing data lowers confidence instead of receiving invented defaults.
- Rental capital value is never confused with monthly rent.

### Phase 6 — Add cost basis, returns, and snapshots

**Work**

- Implement the formulas in section 4.
- Add the transaction ledger and quarterly snapshot job.
- Preserve realized and unrealized results separately.
- Make snapshots idempotent per property/date/model/index version.

**Acceptance**

- Every displayed number can be reconstructed from stored inputs.
- Portfolio totals sum only compatible capital values and return measures.

### Phase 7 — Expose valuation evidence in the UI

**Work**

- Extend frontend types instead of stripping backend metadata.
- Apply the labels and disclosures in section 9.
- Add a valuation detail drawer explaining the formula for one property.

**Acceptance**

- A user can tell the value date, method, uncertainty, and whether the result is current, stale, or forecast.

### Phase 8 — Backtest and shadow launch

**Work**

- Build rolling out-of-time tests and ratio-study reports.
- Run V2 beside the existing engine for at least one full index refresh cycle.
- Compare V2 with actual later listings/sales where available.
- Review large method disagreements manually.

**Acceptance**

- All section 10 gates pass.
- Distribution shifts and fallback rates are understood by asset and district.

### Phase 9 — Production operations

**Work**

- Ingest indices on release; snapshot quarterly; evaluate drift quarterly; consider retraining every six months.
- Promote model/index versions through a registry with rollback.
- Monitor errors, stale coverage, confidence mix, feature drift, and interval calibration.

**Acceptance**

- No model auto-promotes solely because six months elapsed.
- Rollback restores the prior model/index pair without rewriting historical snapshots.

## 12. Recommended delivery order

```text
Definitions and baseline
    -> complete property/financial data
    -> versioned model and index contracts
    -> observed index ingestion
    -> unified valuation service
    -> asset-specific methods
    -> return accounting and snapshots
    -> transparent UI
    -> shadow validation
    -> production rollout
```

The first production milestone should cover **land and houses in supported geographies**. Rental capital valuation should launch after its physical-property fields and operating-income data are available. Until then, show market rent and rental cash flow separately without presenting gross-rent capitalization as a precise current capital value.

## 13. Sources

- Central Bank of Sri Lanka, [Land Valuation Indicator, Second Half of 2025](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/land_valuation_indicator_second_half_of_2025_e.pdf)
- Central Bank of Sri Lanka, [Real Estate Market Analysis, 2024 Q1](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/real_estate_market_analysis_2024_q1.pdf)
- Central Bank of Sri Lanka, [Real Estate Market Analysis, 2026 Q1](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/real_estate_market_analysis_2026_q1.pdf)
- Central Bank of Sri Lanka, [Condominium Market Survey and Real Estate Property Price Indices release archive](https://www.cbsl.gov.lk/en/statistics/business-surveys/condominium-market-survey)
- Central Bank of Sri Lanka, [Staff Studies Vol. 51: Sri Lankan real-estate index coverage and methodology](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/otherpub/staff_studies_Vol_51_2021.pdf)
- Eurostat/ILO/IMF/OECD/UNECE/World Bank, [Handbook on Residential Property Price Indices](https://ec.europa.eu/eurostat/web/products-manuals-and-guidelines/-/ks-ra-12-022)
- Federal Housing Finance Agency, [House Price Index methodology and uses](https://www.fhfa.gov/faqs/hpi)
- International Association of Assessing Officers, [Standard on Automated Valuation Models](https://www.iaao.org/media/standards/Standard_on_Automated_Valuation_Models.pdf)
- International Valuation Standards Council, [Standards glossary](https://ivsc.org/standards-glossary/)
- IFRS Foundation, [IAS 40 Investment Property](https://www.ifrs.org/issued-standards/list-of-standards/ias-40-investment-property/)
- RICS, [Automated Valuation Models roadmap and confidence discussion](https://www.rics.org/content/dam/ricsglobal/documents/standards/rics_avm_roadmap.pdf)
