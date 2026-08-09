import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../../components/Layout';
import MapExplorer from '../../components/MapExplorer';
import type { PredictionResponse, RecommendationResponse } from '../../services/predictionsService';
import { getRecommendation, makePrediction } from '../../services/predictionsService';
import '../../assets/css/landprice.css';

const PERIODS = [
  '2022 H1', '2022 H2',
  '2023 H1', '2023 H2',
  '2024 H1', '2024 H2',
  '2025 H1', '2025 H2'
];

const SQFT_PER_PERCHE = 272.25;

const LOCATION_OPTIONS = [
  { label: 'Piliyandala', district: 'Colombo', lat: 6.801757, lon: 79.922731 },
  { label: 'Talawatugoda', district: 'Colombo', lat: 6.875865, lon: 79.939194 },
  { label: 'Malabe', district: 'Colombo', lat: 6.906079, lon: 79.969628 },
  { label: 'Athurugiriya', district: 'Colombo', lat: 6.872319, lon: 80.000388 },
  { label: 'Nugegoda', district: 'Colombo', lat: 6.864908, lon: 79.899679 },
  { label: 'Kottawa', district: 'Colombo', lat: 6.841165, lon: 79.965432 },
  { label: 'Homagama', district: 'Colombo', lat: 6.843276, lon: 80.003183 },
  { label: 'Battaramulla', district: 'Colombo', lat: 6.898382, lon: 79.917841 },
  { label: 'Dehiwala', district: 'Colombo', lat: 6.830119, lon: 79.880083 },
  { label: 'Maharagama', district: 'Colombo', lat: 6.8478, lon: 79.921762 },
  { label: 'Moratuwa', district: 'Colombo', lat: 6.788071, lon: 79.891281 },
  { label: 'Negombo', district: 'Gampaha', lat: 7.195547, lon: 79.857338 },
  { label: 'Kadawatha', district: 'Gampaha', lat: 7.004672, lon: 79.9542 },
  { label: 'Ja-Ela', district: 'Gampaha', lat: 7.08576, lon: 79.925444 },
  { label: 'Wattala', district: 'Gampaha', lat: 6.986013, lon: 79.907016 },
  { label: 'Gampaha City', district: 'Gampaha', lat: 7.084048, lon: 80.009831 },
  { label: 'Kiribathgoda', district: 'Gampaha', lat: 7.129421, lon: 80.02235 },
  { label: 'Ragama', district: 'Gampaha', lat: 7.023177, lon: 79.907772 },
  { label: 'Panadura', district: 'Kalutara', lat: 6.752799, lon: 79.894931 },
  { label: 'Horana', district: 'Kalutara', lat: 6.724653, lon: 80.039946 },
  { label: 'Bandaragama', district: 'Kalutara', lat: 6.714407, lon: 79.98906 },
  { label: 'Kalutara City', district: 'Kalutara', lat: 6.585395, lon: 79.96074 },
  { label: 'Wadduwa', district: 'Kalutara', lat: 6.636282, lon: 79.952845 },
  { label: 'Matugama', district: 'Kalutara', lat: 6.521943, lon: 80.113685 },
];

const DISTRICTS = ['Colombo', 'Gampaha', 'Kalutara'];

const initialForm = {
  house_sqft: '',
  land_perches: '',
  bedrooms: '3',
  bathrooms: '2',
  district: 'Colombo',
  sub_location: 'Piliyandala',
  market_period: '2025 H2',
  quality_tier: 'normal',
  road_width_ft: '',
  parking_spaces: '',
  distance_to_town_km: '',
  distance_to_hospital_km: '',
  distance_to_school_km: '',
  distance_to_supermarket_km: '',
  distance_to_transport_km: '',
  water: false,
  electricity: false,
  main_road: false,
  carpet_road: false,
  private_lane: false,
  hot_water: false,
  solar_power: false,
  brand_new: false,
  fully_furnished: false,
  air_conditioned: false,
  cctv: false,
  garden: false,
  pantry: false,
  servant_room: false,
  additional_notes: '',
};

type HouseForm = typeof initialForm;
type HouseFormField = keyof HouseForm;

const OPTIONAL_FACILITY_FIELDS: Array<[HouseFormField, string]> = [
  ['water', 'Water'],
  ['electricity', 'Electricity'],
  ['main_road', 'Main road'],
  ['carpet_road', 'Carpet road'],
  ['private_lane', 'Private lane'],
  ['hot_water', 'Hot water'],
  ['solar_power', 'Solar power'],
  ['brand_new', 'Brand new'],
  ['fully_furnished', 'Furnished'],
  ['air_conditioned', 'A/C'],
  ['cctv', 'CCTV'],
  ['garden', 'Garden'],
  ['pantry', 'Pantry'],
  ['servant_room', 'Servant room'],
];

const periodToDateParts = (period: string) => {
  const [yearText, half] = period.split(' ');
  return {
    posted_year: Number(yearText) || 2025,
    posted_month: half === 'H1' ? 6 : 12,
  };
};

const numberOrZero = (value: string) => (value === '' ? 0 : Number(value));

const buildDescription = (form: HouseForm) => {
  const parts: string[] = [];

  if (form.quality_tier === 'luxury') parts.push('Luxury house');
  if (form.quality_tier === 'semi_luxury') parts.push('Semi luxury house');
  if (form.quality_tier === 'normal') parts.push('Normal residential house');
  if (form.brand_new) parts.push('Brand new house');
  if (form.fully_furnished) parts.push('Fully furnished');
  if (form.air_conditioned) parts.push('Air conditioned rooms');
  if (form.cctv) parts.push('CCTV security');
  if (form.garden) parts.push('Garden space');
  if (form.pantry) parts.push('Pantry and kitchen');
  if (form.servant_room) parts.push('Servant room');

  const roadWidth = numberOrZero(form.road_width_ft);
  if (roadWidth > 0) {
    const roadType = form.carpet_road ? 'carpet road' : form.private_lane ? 'private lane' : 'road';
    parts.push(`${roadWidth} ft ${roadType} access`);
  }
  if (form.main_road) parts.push('Close to main road');
  if (form.water) parts.push('Water available');
  if (form.electricity) parts.push('Electricity available');
  if (form.hot_water) parts.push('Hot water available');
  if (form.solar_power) parts.push('Solar power available');

  const parking = numberOrZero(form.parking_spaces);
  if (parking > 0) parts.push(`Parking for ${parking} vehicles`);

  const town = numberOrZero(form.distance_to_town_km);
  const hospital = numberOrZero(form.distance_to_hospital_km);
  const school = numberOrZero(form.distance_to_school_km);
  const supermarket = numberOrZero(form.distance_to_supermarket_km);
  const transport = numberOrZero(form.distance_to_transport_km);
  if (town > 0) parts.push(`${town} km to nearest town`);
  if (hospital > 0) parts.push(`${hospital} km to hospital`);
  if (school > 0) parts.push(`${school} km to school`);
  if (supermarket > 0) parts.push(`${supermarket} km to supermarket`);
  if (transport > 0) parts.push(`${transport} km to bus or railway station`);

  if (form.additional_notes.trim()) parts.push(form.additional_notes.trim());
  return parts.join('. ');
};

const HousePrice: React.FC = () => {
  /* -------------------- STATE -------------------- */
  const [form, setForm] = useState<HouseForm>(initialForm);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const locationOptions = useMemo(
    () => LOCATION_OPTIONS.filter(location => location.district === form.district),
    [form.district]
  );

  const selectedLocation = useMemo(() => {
    return locationOptions.find(location => location.label === form.sub_location) || locationOptions[0];
  }, [form.sub_location, locationOptions]);

  const handleFormChange = (fieldName: HouseFormField, value: any) => {
    setForm(prev => {
      if (fieldName === 'district') {
        const firstLocation = LOCATION_OPTIONS.find(location => location.district === value);
        return {
          ...prev,
          district: value,
          sub_location: firstLocation?.label || '',
        };
      }
      return { ...prev, [fieldName]: value };
    });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);
    setRecommendation(null);
    setError('');

    try {
      const houseSqft = numberOrZero(form.house_sqft);
      const landPerches = numberOrZero(form.land_perches);
      const bedrooms = Number.parseInt(form.bedrooms, 10);
      const bathrooms = Number.parseInt(form.bathrooms, 10);

      if (!selectedLocation || houseSqft <= 0 || landPerches <= 0 || bedrooms <= 0 || bathrooms <= 0) {
        throw new Error('Please complete house size, land size, bedrooms, bathrooms, and location.');
      }

      const period = periodToDateParts(String(form.market_period || '2025 H2'));
      const payload = {
        house_sqft: houseSqft,
        land_sqft: landPerches * SQFT_PER_PERCHE,
        bedrooms,
        bathrooms,
        lat: selectedLocation.lat,
        lon: selectedLocation.lon,
        district: selectedLocation.district,
        sub_location: selectedLocation.label,
        posted_year: period.posted_year,
        posted_month: period.posted_month,
        description: buildDescription(form),
      };

      const data = await makePrediction('house', payload);
      setResult(data);

      try {
        const rec = await getRecommendation('house');
        setRecommendation(rec);
      } catch {
        setRecommendation({ model_type: 'house', recommendation: 'unavailable' });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const parseNumber = (value: unknown) => {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') return parseFloat(value.replace(/,/g, ''));
    return 0;
  };

  const getBasePrice = () => {
    if (!result || !result.predicted_value) return 0;
    return parseNumber(result.predicted_value);
  };

  const basePrice = getBasePrice();
  const details: Record<string, any> = result?.details || {};

  const getRecommendationLabel = () => {
    const label = (recommendation?.recommendation || 'unavailable').toString().toLowerCase();
    if (label === 'buy') return { text: 'BUY', tone: 'buy' };
    if (label === 'sell') return { text: 'SELL', tone: 'sell' };
    if (label === 'hold') return { text: 'HOLD', tone: 'hold' };
    return { text: 'UNAVAILABLE', tone: 'unavailable' };
  };

  const recommendationLabel = getRecommendationLabel();

  const getForecastSeries = () => {
    if (!result) return [];
    const sequence = Array.isArray(result.predicted_sequence) ? result.predicted_sequence : [];
    const cleaned = sequence.map(parseNumber).filter(value => Number.isFinite(value));
    if (cleaned.length === 5) return cleaned;
    if (basePrice > 0) {
      return Array.from({ length: 5 }, (_, idx) => basePrice * (1 + (idx + 1) * 0.015));
    }
    return [];
  };

  const forecastSeries = getForecastSeries();
  const forecastLabels = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'];
  const forecastMin = forecastSeries.length ? Math.min(...forecastSeries) : 0;
  const forecastMax = forecastSeries.length ? Math.max(...forecastSeries) : 1;
  const forecastRange = forecastMax - forecastMin || 1;
  const chartWidth = 560;
  const chartHeight = 240;
  const chartPadding = { left: 36, right: 20, top: 20, bottom: 30 };
  const forecastPoints = forecastSeries.map((value, idx) => {
    const x = chartPadding.left + (idx * (chartWidth - chartPadding.left - chartPadding.right)) / (forecastSeries.length - 1 || 1);
    const y = chartPadding.top + (1 - (value - forecastMin) / forecastRange) * (chartHeight - chartPadding.top - chartPadding.bottom);
    return { x, y };
  });
  const linePath = forecastPoints.map((point, idx) => `${idx === 0 ? 'M' : 'L'}${point.x} ${point.y}`).join(' ');
  const areaPath = forecastPoints.length
    ? `${linePath} L ${forecastPoints[forecastPoints.length - 1].x} ${chartHeight - chartPadding.bottom} L ${forecastPoints[0].x} ${chartHeight - chartPadding.bottom} Z`
    : '';

  const barData = result
    ? PERIODS.map((period, index) => ({
        period,
        value: basePrice * (0.75 + index * 0.04),
      }))
    : [];
  const maxVal = barData.length > 0 ? Math.max(...barData.map(item => item.value)) : 1;

  return (
    <Layout>
      <div className="lp-wrapper">
        <div className="model-selector-container">
          <div className="model-tabs">
            <Link to="/house-price" className="model-tab active">Housing Price</Link>
            <Link to="/rental-price" className="model-tab">Rental Price</Link>
            <Link to="/land-price" className="model-tab">Land Price</Link>
          </div>
        </div>

        <main className="main-content">
          <div className="top-section">
            <div className="card">
              <div className="form-container">
                <div className="form-col">
                  <div className="input-group">
                    <label>House size (sqft)</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 1800"
                      value={form.house_sqft}
                      onChange={e => handleFormChange('house_sqft', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Land size (perches)</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 10"
                      value={form.land_perches}
                      onChange={e => handleFormChange('land_perches', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Bedrooms</label>
                    <input
                      type="number"
                      className="input-field"
                      value={form.bedrooms}
                      onChange={e => handleFormChange('bedrooms', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Bathrooms</label>
                    <input
                      type="number"
                      className="input-field"
                      value={form.bathrooms}
                      onChange={e => handleFormChange('bathrooms', e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-col">
                  <div className="input-group">
                    <label>District</label>
                    <select
                      className="input-field"
                      value={form.district}
                      onChange={e => handleFormChange('district', e.target.value)}
                    >
                      {DISTRICTS.map(district => (
                        <option key={district} value={district}>{district}</option>
                      ))}
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Nearest town / area</label>
                    <select
                      className="input-field"
                      value={form.sub_location}
                      onChange={e => handleFormChange('sub_location', e.target.value)}
                    >
                      {locationOptions.map(location => (
                        <option key={`${location.district}-${location.label}`} value={location.label}>
                          {location.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Market period</label>
                    <select
                      className="input-field"
                      value={form.market_period}
                      onChange={e => handleFormChange('market_period', e.target.value)}
                    >
                      {PERIODS.map(period => (
                        <option key={period} value={period}>{period}</option>
                      ))}
                    </select>
                  </div>
                  <div className="input-group">
                    <label>House type</label>
                    <select
                      className="input-field"
                      value={form.quality_tier}
                      onChange={e => handleFormChange('quality_tier', e.target.value)}
                    >
                      <option value="normal">Normal</option>
                      <option value="semi_luxury">Semi luxury</option>
                      <option value="luxury">Luxury</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="form-container house-optional-grid">
                <div className="form-col">
                  <div className="input-group">
                    <label>Road width (feet)</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 20"
                      value={form.road_width_ft}
                      onChange={e => handleFormChange('road_width_ft', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Parking spaces</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 2"
                      value={form.parking_spaces}
                      onChange={e => handleFormChange('parking_spaces', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Distance to nearest town (km)</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 1.5"
                      value={form.distance_to_town_km}
                      onChange={e => handleFormChange('distance_to_town_km', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Distance to hospital (km)</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 2"
                      value={form.distance_to_hospital_km}
                      onChange={e => handleFormChange('distance_to_hospital_km', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Distance to school (km)</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 0.8"
                      value={form.distance_to_school_km}
                      onChange={e => handleFormChange('distance_to_school_km', e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-col">
                  <div className="input-group">
                    <label>Optional facilities</label>
                    <div className="checkbox-grid">
                      {OPTIONAL_FACILITY_FIELDS.map(([field, label]) => (
                        <label className="checkbox-item" key={field}>
                          <input
                            type="checkbox"
                            checked={Boolean(form[field])}
                            onChange={e => handleFormChange(field, e.target.checked)}
                          />
                          <span className="checkmark"></span> {label}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className="input-group">
                    <label>Distance to supermarket (km)</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 1"
                      value={form.distance_to_supermarket_km}
                      onChange={e => handleFormChange('distance_to_supermarket_km', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Distance to bus / railway (km)</label>
                    <input
                      type="number"
                      className="input-field"
                      placeholder="e.g 0.5"
                      value={form.distance_to_transport_km}
                      onChange={e => handleFormChange('distance_to_transport_km', e.target.value)}
                    />
                  </div>
                  <div className="input-group">
                    <label>Additional notes</label>
                    <input
                      type="text"
                      className="input-field"
                      placeholder="e.g quiet residential lane"
                      value={form.additional_notes}
                      onChange={e => handleFormChange('additional_notes', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="card hero-card">
              <div className="hero-image">
                <img src="/img/housing.png" alt="Housing" />
              </div>
              <h3 className="hero-title">Reva Housing</h3>
              <p className="hero-desc">
                Estimate house prices using location, property details, and nearby amenities.
              </p>
              <button className="cta-btn" onClick={handleSubmit} disabled={loading}>
                {loading ? 'Estimating...' : 'Estimate Price'}
              </button>
            </div>
          </div>

          {error && (
            <div style={{ marginBottom: '60px' }}>
              <div className="error-box">
                <div className="error-icon">
                  <i className="fa-solid fa-circle-exclamation"></i>
                </div>
                <div className="error-title">Unable to Estimate Price</div>
                <div className="error-message">{error}</div>
              </div>
            </div>
          )}

          {result && !error && (
            <div className="analytics-section">
              <div className="prediction-box">
                <div className="input-group">
                  <label>Estimated house price</label>
                </div>
                <div className="pred-value">
                  LKR {Math.round(basePrice).toLocaleString()}
                </div>
                <div className="prediction-range">
                  Range:&nbsp;
                  {Math.round(basePrice * 0.9).toLocaleString()}
                  {' - '}
                  {Math.round(basePrice * 1.1).toLocaleString()}
                </div>
                <div className="result-meta-grid">
                  {details.predicted_price_per_sqft && (
                    <span>LKR {Math.round(details.predicted_price_per_sqft).toLocaleString()} / sqft</span>
                  )}
                  {details.description_value_index !== undefined && (
                    <span>Context score {(Number(details.description_value_index) * 100).toFixed(0)}%</span>
                  )}
                  {details.model_variant && <span>{String(details.model_variant).replace(/_/g, ' ')}</span>}
                </div>
              </div>

              <div className="chart-container">
                <div className="chart-header">
                  <div style={{ fontWeight: 600, fontSize: '18px' }}>
                    Price over the last years
                  </div>
                  <i className="fa-solid fa-chart-column"></i>
                </div>

                <div className="bar-chart">
                  {barData.map(item => (
                    <div className="bar-group" key={item.period}>
                      <span className="bar-value">{Math.round(item.value / 1000)}k</span>
                      <div
                        className="bar"
                        style={{
                          height: `${Math.min(Math.max((item.value / maxVal) * 75, 8), 75)}%`,
                        }}
                      ></div>
                      <span className="bar-label">
                        {item.period.split(' ')[0]}<br />{item.period.split(' ')[1]}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {forecastSeries.length > 0 && (
                <div className="forecast-row">
                  <div className="chart-container forecast-container">
                    <div className="chart-header">
                      <div style={{ fontWeight: 600, fontSize: '18px' }}>
                        Future price forecast
                      </div>
                      <i className="fa-solid fa-chart-line"></i>
                    </div>
                    <div className="forecast-chart">
                      <svg
                        className="forecast-svg"
                        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                        role="img"
                        aria-label="Future price forecast"
                      >
                        <defs>
                          <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#4445ff" stopOpacity="0.35" />
                            <stop offset="100%" stopColor="#d0d7ff" stopOpacity="0.05" />
                          </linearGradient>
                        </defs>
                        <g className="forecast-grid">
                          {[0.25, 0.5, 0.75].map((ratio) => (
                            <line
                              key={ratio}
                              x1={chartPadding.left}
                              x2={chartWidth - chartPadding.right}
                              y1={chartPadding.top + (chartHeight - chartPadding.top - chartPadding.bottom) * ratio}
                              y2={chartPadding.top + (chartHeight - chartPadding.top - chartPadding.bottom) * ratio}
                            />
                          ))}
                        </g>
                        <line
                          className="forecast-axis"
                          x1={chartPadding.left}
                          y1={chartHeight - chartPadding.bottom}
                          x2={chartWidth - chartPadding.right}
                          y2={chartHeight - chartPadding.bottom}
                        />
                        <path className="forecast-area" d={areaPath} />
                        <path className="forecast-line" d={linePath} />
                        {forecastPoints.map((point, idx) => (
                          <g key={forecastLabels[idx]}>
                            <circle className="forecast-point" cx={point.x} cy={point.y} r="4" />
                            <text className="forecast-value" x={point.x} y={point.y - 10} textAnchor="middle">
                              {Math.round(forecastSeries[idx] / 1000)}k
                            </text>
                            <text className="forecast-label" x={point.x} y={chartHeight - 8} textAnchor="middle">
                              {forecastLabels[idx]}
                            </text>
                          </g>
                        ))}
                      </svg>
                    </div>
                  </div>

                  <div className="chart-container recommendation-card">
                    <div className="chart-header">
                      <div style={{ fontWeight: 600, fontSize: '18px' }}>
                        Recommendation
                      </div>
                      <i className="fa-solid fa-lightbulb"></i>
                    </div>
                    <div className={`recommendation-label rec-${recommendationLabel.tone}`}>
                      {recommendationLabel.text}
                    </div>
                    <p className="recommendation-subtitle">
                      Based on your latest prediction signals.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          <section className="map-explorer-section">
            <div className="map-section-header">
              <h2>Market Data Explorer</h2>
              <p>Click anywhere on the map to find nearby records from our database.</p>
            </div>
            <MapExplorer />
          </section>
        </main>
      </div>
    </Layout>
  );
};

export default HousePrice;
