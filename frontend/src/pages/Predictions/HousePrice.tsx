import React from 'react';
import { Link } from 'react-router-dom';
import Layout from '../../components/Layout';
import Footer from '../../components/Footer';
import MapExplorer from '../../components/MapExplorer';

const LandPrice: React.FC = () => {
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
                                <input type="number" className="input-field" placeholder="e.g 20.0" />
                            </div>
                            <div className="input-group">
                                <label>District</label>
                                <select className="input-field">
                                    <option>Select District</option>
                                    <option>Colombo</option>
                                    <option>Gampaha</option>
                                    <option>Kandy</option>
                                    <option>Galle</option>
                                </select>
                            </div>
                            <div className="input-group mt-auto">
                                <label>Location / Town / Landmarks</label>
                                <input type="text" className="input-field" placeholder="e.g Kiribathgoda" />
                            </div>
                        </div>

                        <div className="form-col">
                            <div className="input-group">
                                <label>Other utilities</label>
                                <div className="checkbox-grid">
                                    <label className="checkbox-item"><input type="checkbox"/><span className="checkmark"></span> Main road</label>
                                    <label className="checkbox-item"><input type="checkbox"/><span className="checkmark"></span> Electricity</label>
                                    <label className="checkbox-item"><input type="checkbox"/><span className="checkmark"></span> Clear deed</label>
                                    <label className="checkbox-item"><input type="checkbox"/><span className="checkmark"></span> Water</label>
                                    <label className="checkbox-item"><input type="checkbox"/><span className="checkmark"></span> Bank loan</label>
                                    <label className="checkbox-item"><input type="checkbox"/><span className="checkmark"></span> Near town</label>
                                </div>
                            </div>
                            <div className="input-group mt-auto"> 
                                <label>Distance to nearest town (meters)</label>
                                <input type="number" className="input-field" placeholder="e.g 500" />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="card hero-card">
                    <div className="hero-image"><img src="/img/lands.png" alt="Lands" /></div>
                    <h3 className="hero-title">Rēva Lands</h3>
                    <p className="hero-desc">Ask Rēva to estimate land prices using real-time location intelligence.</p>
                    <button className="cta-btn">Estimate Price</button>
                </div>
            </div>

            {/* ANALYTICS SECTION */}
            <div className="analytics-section">
                <div className="prediction-box">
                    <div className="input-group"><label>Estimated value for perch</label></div>
                    <div className="pred-value">LKR 1,250,000</div>
                    <div style={{fontSize: '13px', color:'var(--success-green)', background:'var(--success-bg)', padding:'8px 16px', borderRadius:'8px', width:'fit-content', fontWeight:600}}>
                        <i className="fa-solid fa-check-circle"></i> Range: 1,125,000 - 1,375,000
                    </div>
                </div>

                <div className="chart-container">
                    <div className="chart-header">
                        <div style={{fontWeight:600, fontSize:'18px'}}>Price over the last years</div>
                        <i className="fa-solid fa-chart-column" style={{color:'#9A9AB0', fontSize: '20px'}}></i>
                    </div>

                    <div className="bar-chart">
                        {/* Note: In React, we replace "style='height:45%'" with style={{height:'45%'}}.
                           I am keeping the HTML structure exactly as requested.
                        */}
                        <div className="bar-group"><span className="bar-value">350k</span><div className="bar" style={{height:'45%'}}></div><span className="bar-label">2022<br/>H1</span></div>
                        <div className="bar-group"><span className="bar-value">600k</span><div className="bar" style={{height:'85%'}}></div><span className="bar-label">2022<br/>H2</span></div>
                        <div className="bar-group"><span className="bar-value">350k</span><div className="bar" style={{height:'45%'}}></div><span className="bar-label">2023<br/>H1</span></div>
                        <div className="bar-group"><span className="bar-value">600k</span><div className="bar" style={{height:'85%'}}></div><span className="bar-label">2023<br/>H2</span></div>
                        <div className="bar-group"><span className="bar-value">350k</span><div className="bar" style={{height:'45%'}}></div><span className="bar-label">2024<br/>H1</span></div>
                        <div className="bar-group"><span className="bar-value">600k</span><div className="bar" style={{height:'85%'}}></div><span className="bar-label">2024<br/>H2</span></div>
                        <div className="bar-group"><span className="bar-value">350k</span><div className="bar" style={{height:'45%'}}></div><span className="bar-label">2025<br/>H1</span></div>
                        <div className="bar-group"><span className="bar-value">600k</span><div className="bar" style={{height:'60%'}}></div><span className="bar-label">2025<br/>H2</span></div>
                    </div>
                </div>
            </div>

            {/* MAP EXPLORER SECTION (Reusing our component!) */}
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