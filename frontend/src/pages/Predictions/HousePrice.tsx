import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../../components/Layout';
import Footer from '../../components/Footer';
import MapExplorer from '../../components/MapExplorer';
import type { Feature } from '../../services/predictionsService';
import { getFeatures, makePrediction } from '../../services/predictionsService';

const PERIODS = [
  '2022 H1', '2022 H2',
  '2023 H1', '2023 H2',
  '2024 H1', '2024 H2',
  '2025 H1', '2025 H2'
];

const HousePrice: React.FC = () => {
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
        const data = await getFeatures('house');
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

      const data = await makePrediction('house', payload);
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
            <Link to="/house-price" className="model-tab active">Housing Price</Link>
            <Link to="/rental-price" className="model-tab">Rental Price</Link>
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
                <img src="/img/housing.png" alt="Housing" />
              </div>
              <h3 className="hero-title">Rēva Housing</h3>
              <p className="hero-desc">
                Ask Rēva to estimate house prices using real-time market intelligence.
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
                  <label>Estimated house price</label>
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

        <Footer />
      </div>
    </Layout>
  );
};

export default HousePrice;