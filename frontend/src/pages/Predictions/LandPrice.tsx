import React, { useState } from 'react';
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

const LandPrice: React.FC = () => {
  /* -------------------- STATE -------------------- */
  const [form, setForm] = useState<Record<string, any>>({
    land_size: '',
    district: '',
    location_text: '',
    main_road: false,
    electricity: false,
    clear_deed: false,
    water: false,
    bank_loan: false,
    near_town: false,
    distance_to_town_m: '',
    period: '2025 H2',
  });
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  /* -------------------- HANDLERS -------------------- */
  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);
    setRecommendation(null);
    setError('');

    try {
      const payload = {
        land_size: form.land_size === '' ? 0 : parseFloat(form.land_size),
        district: String(form.district || '').trim(),
        location_text: String(form.location_text || '').trim(),
        main_road: Boolean(form.main_road),
        electricity: Boolean(form.electricity),
        clear_deed: Boolean(form.clear_deed),
        water: Boolean(form.water),
        bank_loan: Boolean(form.bank_loan),
        near_town: Boolean(form.near_town),
        distance_to_town_m: form.distance_to_town_m === '' ? 0 : parseFloat(form.distance_to_town_m),
        period: String(form.period || '2025 H2'),
      };

      const data = await makePrediction('land', payload);
      setResult(data);

      try {
        const rec = await getRecommendation('land');
        setRecommendation(rec);
      } catch {
        setRecommendation({ model_type: 'land', recommendation: 'unavailable' });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFormChange = (fieldName: string, value: any) => {
    setForm(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  /* -------------------- FIXED MOCK BAR DATA -------------------- */
  // Helper to ensure we have a valid number
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
    ? PERIODS.map((p, i) => ({
        period: p,
        value: basePrice * (0.75 + i * 0.04) 
      }))
    : [];

  const maxVal =
    barData.length > 0
        ? Math.max(...barData.map(b => b.value))
        : 1;

  return (
    <Layout>
      <div className="lp-wrapper">

        {/* MODEL SELECTOR TABS */}
        <div className="model-selector-container">
          <div className="model-tabs">
            <Link to="/house-price" className="model-tab">Housing Price</Link>
            <Link to="/rental-price" className="model-tab">Rental Price</Link>
            <Link to="/land-price" className="model-tab active">Land Price</Link>
          </div>
        </div>

        <main className="main-content">
          {/* Mobile-only Top Hero Section */}
          <div className="mobile-prediction-hero">
            <div className="hero-image">
              <img src="/img/lands.png" alt="Land" />
            </div>
            <h1 className="hero-title">Reva Land</h1>
            <p className="hero-desc">
              Estimate land prices using location, plot size, and nearby facilities.
            </p>
          </div>

          {/* INPUT FORM SECTION */}
          <div className="top-section">
            <div className="card">
              <div className="form-container">
                {/* Land Size */}
                <div className="input-group">
                  <label>Land size (perches)</label>
                  <input 
                    type="number" 
                    className="input-field" 
                    placeholder="e.g 20.0"
                    value={form['land_size'] || ''}
                    onChange={e => handleFormChange('land_size', e.target.value)}
                  />
                </div>

                {/* Other Utilities (grid-row: span 2) */}
                <div className="input-group other-utilities-group">
                  <label>Other utilities</label>
                  <div className="checkbox-grid">
                    <label className="checkbox-item">
                      <input type="checkbox" checked={form['main_road'] || false} onChange={e => handleFormChange('main_road', e.target.checked)} />
                      <span className="checkmark"></span> Main road
                    </label>
                    <label className="checkbox-item">
                      <input type="checkbox" checked={form['electricity'] || false} onChange={e => handleFormChange('electricity', e.target.checked)} />
                      <span className="checkmark"></span> Electricity
                    </label>
                    <label className="checkbox-item">
                      <input type="checkbox" checked={form['clear_deed'] || false} onChange={e => handleFormChange('clear_deed', e.target.checked)} />
                      <span className="checkmark"></span> Clear deed
                    </label>
                    <label className="checkbox-item">
                      <input type="checkbox" checked={form['water'] || false} onChange={e => handleFormChange('water', e.target.checked)} />
                      <span className="checkmark"></span> Water
                    </label>
                    <label className="checkbox-item">
                      <input type="checkbox" checked={form['bank_loan'] || false} onChange={e => handleFormChange('bank_loan', e.target.checked)} />
                      <span className="checkmark"></span> Bank loan
                    </label>
                    <label className="checkbox-item">
                      <input type="checkbox" checked={form['near_town'] || false} onChange={e => handleFormChange('near_town', e.target.checked)} />
                      <span className="checkmark"></span> Near town
                    </label>
                  </div>
                </div>

                {/* District */}
                <div className="input-group">
                  <label>District</label>
                  <select 
                    className="input-field"
                    value={form['district'] || ''}
                    onChange={e => handleFormChange('district', e.target.value)}
                  >
                    <option value="">Select District</option>
                    <option value="Colombo">Colombo</option>
                    <option value="Gampaha">Gampaha</option>
                    <option value="Kandy">Kandy</option>
                    <option value="Galle">Galle</option>
                  </select>
                </div>

                {/* Location */}
                <div className="input-group">
                  <label>Location / Town / Landmarks</label>
                  <input 
                    type="text" 
                    className="input-field" 
                    placeholder="e.g Kiribathgoda"
                    value={form['location_text'] || ''}
                    onChange={e => handleFormChange('location_text', e.target.value)}
                  />
                </div>

                {/* Distance to nearest town */}
                <div className="input-group">
                  <label>Distance to nearest town (meters)</label>
                  <input 
                    type="number" 
                    className="input-field" 
                    placeholder="e.g 500"
                    value={form['distance_to_town_m'] || ''}
                    onChange={e => handleFormChange('distance_to_town_m', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* HERO CARD */}
            <div className="card hero-card">
              <div className="hero-image">
                <img src="/img/lands.png" alt="Lands" />
              </div>
              <h3 className="hero-title">Reva Lands</h3>
              <p className="hero-desc">
                Ask Reva to estimate land prices using real-time location intelligence.
              </p>
              <button className="cta-btn" onClick={handleSubmit} disabled={loading}>
                {loading ? 'Estimating...' : 'Estimate Price'}
              </button>
            </div>
          </div>

          {/* ANALYTICS SECTION */}
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
                  <label>Estimated value for perch</label>
                </div>
                <div className="pred-value">
                  LKR {Math.round(basePrice).toLocaleString()}
                </div>
                <div style={{
                  fontSize: '13px',
                  color: 'var(--success-green)',
                  background: 'var(--success-bg)',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  width: 'fit-content',
                  fontWeight: 600
                }}>
                  Range:&nbsp;
                  {Math.round(basePrice * 0.9).toLocaleString()}
                  {' - '}
                  {Math.round(basePrice * 1.1).toLocaleString()}
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
                  {barData.map(b => (
                    <div className="bar-group" key={b.period}>
                      <span className="bar-value">
                        {Math.round(b.value / 1000)}k
                      </span>
                      {/* FIX: Changed max scaling to 75%. 
                         This ensures the bar (max 75%) + Value Text + Label Text 
                         fits within the 100% height container without flex shrinking.
                      */}
                      <div
                        className="bar"
                        style={{
                            height: `${Math.min(
                            Math.max((b.value / maxVal) * 75, 8), // Scale to max 75%
                            75
                            )}%`
                        }}
                        ></div>

                      <span className="bar-label">
                        {b.period.split(' ')[0]}<br />{b.period.split(' ')[1]}
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

          {/* MAP SECTION */}
          <section className="map-explorer-section">
            <div className="map-section-header">
              <h2>Market Data Explorer</h2>
              <p>Click anywhere on the map to find nearby records from our database.</p>
            </div>
            <MapExplorer pageType="land" />
          </section>

        </main>
      </div>
    </Layout>
  );
};

export default LandPrice;

