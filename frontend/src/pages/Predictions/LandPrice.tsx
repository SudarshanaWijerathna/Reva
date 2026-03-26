import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../../components/Layout';
import MapExplorer from '../../components/MapExplorer';
import type { Feature } from '../../services/predictionsService';
import { getFeatures, makePrediction } from '../../services/predictionsService';
import '../../assets/css/landprice.css';

const PERIODS = [
  '2022 H1', '2022 H2',
  '2023 H1', '2023 H2',
  '2024 H1', '2024 H2',
  '2025 H1', '2025 H2'
];

const LandPrice: React.FC = () => {
  /* -------------------- STATE -------------------- */
  const [features, setFeatures] = useState<Feature[]>([]);
  const [form, setForm] = useState<Record<string, any>>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [featuresLoading, setFeaturesLoading] = useState(true);
  const [error, setError] = useState<string>('');

  /* -------------------- EFFECTS -------------------- */
  useEffect(() => {
    const loadFeatures = async () => {
      try {
        setFeaturesLoading(true);
        setError('');
        const data = await getFeatures('land');
        setFeatures(data);
        
        // Initialize form with default values based on feature types
        const initialForm: Record<string, any> = {};
        data.forEach(feature => {
          if (feature.data_type === 'boolean') {
            initialForm[feature.name] = false;
          } else if (feature.data_type === 'int' || feature.data_type === 'float') {
            initialForm[feature.name] = '';
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

      const data = await makePrediction('land', payload);
      setResult(data);
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
  const getBasePrice = () => {
    if (!result || !result.predicted_value) return 0;
    const val = result.predicted_value;
    return typeof val === 'string' ? parseFloat(val.replace(/,/g, '')) : val;
  };

  const basePrice = getBasePrice();

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
            <Link to="/rental-price" className="model-tab">Rental Price</Link>
            <Link to="/land-price" className="model-tab active">Land Price</Link>
          </div>
        </div>

        <main className="main-content">

          {/* INPUT FORM SECTION */}
          <div className="top-section">
            <div className="card">
              <div className="form-container">
                <div className="form-col">
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
                  <div className="input-group mt-auto">
                    <label>Location / Town / Landmarks</label>
                    <input 
                      type="text" 
                      className="input-field" 
                      placeholder="e.g Kiribathgoda"
                      value={form['location'] || ''}
                      onChange={e => handleFormChange('location', e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-col">
                  <div className="input-group">
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
                  <div className="input-group mt-auto"> 
                    <label>Distance to nearest town (meters)</label>
                    <input 
                      type="number" 
                      className="input-field" 
                      placeholder="e.g 500"
                      value={form['distance_to_town'] || ''}
                      onChange={e => handleFormChange('distance_to_town', e.target.value)}
                    />
                  </div>
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
            </div>
          )}

          {/* MAP SECTION */}
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

export default LandPrice;

