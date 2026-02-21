import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../../components/Layout';
import Footer from '../../components/Footer';
import MapExplorer from '../../components/MapExplorer';

const PERIODS = [
  '2022 H1', '2022 H2',
  '2023 H1', '2023 H2',
  '2024 H1', '2024 H2',
  '2025 H1', '2025 H2'
];

const LandPrice: React.FC = () => {
  /* -------------------- STATE -------------------- */
  const [form, setForm] = useState({
    land_size: '',
    district: '',
    location_text: '',
    main_road: false,
    electricity: false,
    clear_deed: false,
    water: false,
    bank_loan: false,
    near_town: false,
    distance_to_town_m: ''
  });

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  /* -------------------- HANDLERS -------------------- */
  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);

    const payload = {
      land_size: Number(form.land_size),
      district: form.district,
      location_text: form.location_text,
      main_road: form.main_road,
      clear_deed: form.clear_deed,
      bank_loan: form.bank_loan,
      electricity: form.electricity,
      water: form.water,
      near_town: form.near_town,
      distance_to_town_m: form.near_town
        ? Number(form.distance_to_town_m)
        : 0
    };

    try {
      const res = await fetch('https://reva-olaf.onrender.com/predict/land', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert('Failed to connect to backend');
    } finally {
      setLoading(false);
    }
  };


  /* -------------------- FIXED MOCK BAR DATA -------------------- */
  // Helper to ensure we have a valid number
  const getBasePrice = () => {
    if (!result || !result.adjusted_price_per_perch) return 0;
    // Handle string inputs like "1,000,000" just in case
    const val = result.adjusted_price_per_perch;
    return typeof val === 'string' ? parseFloat(val.replace(/,/g, '')) : val;
  };

  const basePrice = getBasePrice();

  const barData = result
    ? PERIODS.map((p, i) => ({
        period: p,
        // Linear growth simulation
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
                      value={form.land_size}
                      onChange={e => setForm({ ...form, land_size: e.target.value })}
                    />
                  </div>

                  <div className="input-group">
                    <label>District</label>
                    <select
                      className="input-field"
                      value={form.district}
                      onChange={e => setForm({ ...form, district: e.target.value })}
                    >
                      <option value="">Select District</option>
                      <option>Colombo</option>
                      <option>Gampaha</option>
                      <option>Kalutara</option>
                    </select>
                  </div>

                  <div className="input-group mt-auto">
                    <label>Location / Town / Landmarks</label>
                    <input
                      type="text"
                      className="input-field"
                      value={form.location_text}
                      onChange={e => setForm({ ...form, location_text: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-col">
                  <div className="input-group">
                    <label>Other utilities</label>
                    <div className="checkbox-grid">
                      {[
                        ['main_road', 'Main road'],
                        ['electricity', 'Electricity'],
                        ['clear_deed', 'Clear deed'],
                        ['water', 'Water'],
                        ['bank_loan', 'Bank loan'],
                        ['near_town', 'Near town']
                      ].map(([key, label]) => (
                        <label className="checkbox-item" key={key}>
                          <input
                            type="checkbox"
                            checked={(form as any)[key]}
                            onChange={e =>
                              setForm({ ...form, [key]: e.target.checked })
                            }
                          />
                          <span className="checkmark"></span> {label}
                        </label>
                      ))}
                    </div>
                  </div>

                  {form.near_town && (
                    <div className="input-group mt-auto">
                      <label>Distance to nearest town (meters)</label>
                      <input
                        type="number"
                        className="input-field"
                        value={form.distance_to_town_m}
                        onChange={e =>
                          setForm({ ...form, distance_to_town_m: e.target.value })
                        }
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* HERO CARD */}
            <div className="card hero-card">
              <div className="hero-image">
                <img src="/img/lands.png" alt="Lands" />
              </div>
              <h3 className="hero-title">Rēva Lands</h3>
              <p className="hero-desc">
                Ask Rēva to estimate land prices using real-time location intelligence.
              </p>
              <button className="cta-btn" onClick={handleSubmit} disabled={loading}>
                {loading ? 'Estimating...' : 'Estimate Price'}
              </button>
            </div>
          </div>

          {/* ANALYTICS SECTION */}
          {result && (
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

        <Footer />
      </div>
    </Layout>
  );
};

export default LandPrice;