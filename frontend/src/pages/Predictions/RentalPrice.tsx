import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../../components/Layout';
import MapExplorer from '../../components/MapExplorer';
import type { Feature, PredictionResponse, RecommendationResponse } from '../../services/predictionsService';
import { getFeatures, getRecommendation, makePrediction } from '../../services/predictionsService';
import '../../assets/css/landprice.css';

const PERIODS = [
  '2022 H1', '2022 H2',
  '2023 H1', '2023 H2',
  '2024 H1', '2024 H2',
  '2025 H1', '2025 H2'
];

const DEFAULT_SELECT_VALUES: Record<string, string> = {
  property_type: 'Apartment',
  location: 'Colombo 5',
  district: 'Colombo',
  furnishing_status: 'furnished',
};

const RentalPrice: React.FC = () => {
  /* -------------------- STATE -------------------- */
  const [features, setFeatures] = useState<Feature[]>([]);
  const [form, setForm] = useState<Record<string, any>>({});
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [featuresLoading, setFeaturesLoading] = useState(true);
  const [error, setError] = useState<string>('');

  /* -------------------- EFFECTS -------------------- */
  useEffect(() => {
    const loadFeatures = async () => {
      try {
        setFeaturesLoading(true);
        setError('');
        const data = await getFeatures('rental');
        setFeatures(data);
        
        // Initialize form with default values based on feature types
        const initialForm: Record<string, any> = {};
        data.forEach(feature => {
          if (feature.data_type === 'boolean') {
            initialForm[feature.name] = false;
          } else if (feature.data_type === 'int' || feature.data_type === 'float') {
            initialForm[feature.name] = '';
          } else if (feature.options && feature.options.length > 0) {
            const preferredValue = DEFAULT_SELECT_VALUES[feature.name];
            initialForm[feature.name] =
              preferredValue && feature.options.includes(preferredValue)
                ? preferredValue
                : feature.options[0];
          } else {
            initialForm[feature.name] = '';
          }
        });
        setForm(initialForm);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load features');
      } finally {
        setFeaturesLoading(false);
      }
    };

    loadFeatures();
  }, []);

  /* -------------------- HANDLERS -------------------- */
  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);
    setRecommendation(null);
    setError('');

    try {
      // Build payload with correct types
      const payload: Record<string, any> = {};
      features.forEach(feature => {
        const value = form[feature.name];
        
        if (feature.data_type === 'int') {
          payload[feature.name] = value === '' ? 0 : Number(value);
        } else if (feature.data_type === 'float') {
          payload[feature.name] = value === '' ? 0.0 : parseFloat(value);
        } else if (feature.data_type === 'boolean') {
          payload[feature.name] = Boolean(value);
        } else {
          payload[feature.name] = value;
        }
      });

      const data = await makePrediction('rental', payload);
      setResult(data);

      try {
        const rec = await getRecommendation('rental');
        setRecommendation(rec);
      } catch {
        setRecommendation({ model_type: 'rental', recommendation: 'unavailable' });
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

  // Helper to render form field based on data type
  const renderFormField = (feature: Feature) => {
    const value = form[feature.name];

    if (feature.data_type === 'boolean') {
      return (
        <label className="checkbox-item" key={feature.name}>
          <input
            type="checkbox"
            checked={value || false}
            onChange={e => handleFormChange(feature.name, e.target.checked)}
          />
          <span className="checkmark"></span> {feature.label}
        </label>
      );
    } else if (feature.data_type === 'string') {
      if (feature.options && feature.options.length > 0) {
        return (
          <div className="input-group" key={feature.name}>
            <label>{feature.label}</label>
            <select
              className="input-field"
              value={value || ''}
              onChange={e => handleFormChange(feature.name, e.target.value)}
            >
              {feature.options.map(option => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        );
      }
      return (
        <div className="input-group" key={feature.name}>
          <label>{feature.label}</label>
          <input
            type="text"
            className="input-field"
            value={value || ''}
            onChange={e => handleFormChange(feature.name, e.target.value)}
          />
        </div>
      );
    } else if (feature.data_type === 'int' || feature.data_type === 'float') {
      return (
        <div className="input-group" key={feature.name}>
          <label>{feature.label}</label>
          <input
            type="number"
            className="input-field"
            value={value === '' ? '' : value}
            onChange={e => handleFormChange(feature.name, e.target.value)}
          />
        </div>
      );
    }
  };

  // Group features by type for better layout
  const booleanFeatures = features.filter(f => f.data_type === 'boolean');
  const stringFeatures = features.filter(f => f.data_type === 'string');
  const numericFeatures = features.filter(f => f.data_type === 'int' || f.data_type === 'float');

  return (
    <Layout>
      <div className="lp-wrapper">

        {/* MODEL SELECTOR TABS */}
        <div className="model-selector-container">
          <div className="model-tabs">
            <Link to="/house-price" className="model-tab">Housing Price</Link>
            <Link to="/rental-price" className="model-tab active">Rental Price</Link>
            <Link to="/land-price" className="model-tab">Land Price</Link>
          </div>
        </div>

        <main className="main-content">

          {/* INPUT FORM SECTION */}
          <div className="top-section">
            <div className="card">
              {featuresLoading ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-gray)' }}>
                  <i className="fa-solid fa-spinner fa-spin" style={{ fontSize: '32px', marginBottom: '16px' }}></i>
                  <p>Loading form fields...</p>
                </div>
              ) : features.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-gray)' }}>
                  <i className="fa-solid fa-inbox" style={{ fontSize: '32px', marginBottom: '16px' }}></i>
                  <p>No form fields available</p>
                </div>
              ) : (
                <div className="form-container">
                  <div className="form-col">
                    {stringFeatures.map(renderFormField)}
                    {numericFeatures.map(renderFormField)}
                  </div>

                  <div className="form-col">
                    {booleanFeatures.length > 0 && (
                      <div className="input-group">
                        <label>Properties</label>
                        <div className="checkbox-grid">
                          {booleanFeatures.map(renderFormField)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* HERO CARD */}
            <div className="card hero-card">
              <div className="hero-image">
                <img src="/img/rentals.png" alt="Rentals" />
              </div>
              <h3 className="hero-title">Reva Rentals</h3>
              <p className="hero-desc">
                Ask Reva to estimate rental prices using real-time market intelligence.
              </p>
              <button className="cta-btn" onClick={handleSubmit} disabled={loading || featuresLoading}>
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
                  <label>Estimated monthly rental</label>
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
                      <div
                        className="bar"
                        style={{
                            height: `${Math.min(
                            Math.max((b.value / maxVal) * 75, 8),
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
            <MapExplorer pageType="rental" />
          </section>

        </main>

      </div>
    </Layout>
  );
};

export default RentalPrice;

