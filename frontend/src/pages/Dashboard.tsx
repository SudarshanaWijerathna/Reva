import React from 'react';
import Layout from '../components/Layout';
import Footer from '../components/Footer';

const Dashboard: React.FC = () => {
  return (
    <Layout>
      <div className="dashboard-wrapper">
        
        {/* HEADER */}
        <div className="dash-header">
            <div>
                <h1>My Property Portfolio</h1>
                <p>Track your real estate assets and monitor market value changes.</p>
            </div>
            <a href="#" className="btn-primary" title="Add a new property to track and analyze">
                <i className="fa-solid fa-plus"></i> New Property
            </a>
        </div>

        <div className="main-content">
            
            {/* FINANCIAL GRID */}
            <div className="financial-grid">
                <div className="fin-card">
                    <div className="fin-label"><i className="fa-solid fa-sack-dollar"></i> Portfolio Value</div>
                    <div className="fin-value">94.1M</div>
                    <div className="fin-sub text-green"><i className="fa-solid fa-arrow-trend-up"></i> +8.5% overall</div>
                </div>
                
                <div className="fin-card">
                    <div className="fin-label"><i className="fa-solid fa-hand-holding-dollar"></i> Total Profit</div>
                    <div className="fin-value">8.5M</div>
                    <div className="fin-sub text-green">Unrealized gains</div>
                </div>
                
                <div className="fin-card">
                    <div className="fin-label"><i className="fa-regular fa-face-smile"></i> Sentiment</div>
                    <div className="fin-value">Positive</div>
                    <div className="fin-sub text-green">Market looks good</div>
                </div>

                <div className="fin-card">
                    <div className="fin-label"><i className="fa-solid fa-layer-group"></i> Property Mix</div>
                    <ul className="prop-mix-list">
                        <li className="prop-mix-item">
                            <span><i className="fa-solid fa-house"></i> Housing</span>
                            <strong>3 Units</strong>
                        </li>
                        <li className="prop-mix-item">
                            <span><i className="fa-solid fa-building"></i> Rentals</span>
                            <strong>5 Units</strong>
                        </li>
                        <li className="prop-mix-item">
                            <span><i className="fa-solid fa-tree"></i> Lands</span>
                            <strong>2 Plots</strong>
                        </li>
                    </ul>
                </div>
            </div>

            {/* INSIGHT SECTION */}
            <div className="insight-row">
                <div className="insight-card">
                    <div className="insight-header">
                        <i className="fa-solid fa-robot"></i>
                        <h4>Rēva Insight</h4>
                    </div>
                    <div className="insight-text">
                        "Your land in Malabe is showing strong positive sentiment due to recent infrastructure development. Holding for another 6-12 months may yield higher returns. Meanwhile, rental demand in Colombo 03 has slightly cooled off this quarter."
                    </div>
                </div>
            </div>

            {/* HISTORY / TABLE CARD */}
            <div className="history-card">
                <div className="card-title">
                    <div className="card-title-group">
                        <h3>Your Properties</h3>
                        <span className="card-subtitle"><i className="fa-solid fa-circle-info"></i> Valuations estimated using Rēva ML models (Data: Oct 2025)</span>
                    </div>
                    
                    <select className="dashboard-filter" defaultValue="all">
                        <option value="all">View All</option>
                        <option value="housing">Housing</option>
                        <option value="rental">Rental</option>
                        <option value="land">Land</option>
                    </select>
                </div>

                <div className="table-responsive">
                    <table className="reva-table">
                        <thead>
                            <tr>
                                <th>Listed Date</th>
                                <th>Type</th>
                                <th>Location</th>
                                <th>Bought Price</th>
                                <th>Current Val <i className="fa-solid fa-circle-info info-icon" title="Predicted by Rēva AI"></i></th>
                                <th>Profit</th>
                                <th>Sentiment</th>
                                <th>Status</th>
                                <th style={{textAlign: 'right'}}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Oct 24, 2025</td>
                                <td><i className="fa-solid fa-tree type-icon"></i> Land</td>
                                <td>Malabe, Kahanthota</td>
                                <td>10.5M</td>
                                <td>12.0M</td>
                                <td className="text-green">+1.5M</td>
                                <td>
                                    <div className="sentiment-box sent-up">
                                        <i className="fa-solid fa-arrow-trend-up"></i> High
                                    </div>
                                </td>
                                <td><span className="status-badge status-active">Active</span></td>
                                <td>
                                    <div className="action-icons">
                                        <button className="btn-icon" title="Edit"><i className="fa-solid fa-pen-to-square"></i></button>
                                        <button className="btn-icon delete" title="Delete"><i className="fa-solid fa-trash-can"></i></button>
                                    </div>
                                </td>
                            </tr>

                            <tr>
                                <td>Sep 12, 2025</td>
                                <td><i className="fa-solid fa-house type-icon"></i> House</td>
                                <td>Nugegoda, Mirihana</td>
                                <td>42.0M</td>
                                <td>45.5M</td>
                                <td className="text-green">+3.5M</td>
                                <td>
                                    <div className="sentiment-box sent-up">
                                        <i className="fa-solid fa-arrow-trend-up"></i> Positive
                                    </div>
                                </td>
                                <td><span className="status-badge status-active">Active</span></td>
                                <td>
                                    <div className="action-icons">
                                        <button className="btn-icon" title="Edit"><i className="fa-solid fa-pen-to-square"></i></button>
                                        <button className="btn-icon delete" title="Delete"><i className="fa-solid fa-trash-can"></i></button>
                                    </div>
                                </td>
                            </tr>

                            <tr>
                                <td>Aug 05, 2025</td>
                                <td><i className="fa-solid fa-building type-icon"></i> Rental</td>
                                <td>Colombo 03, Kollupitiya</td>
                                <td>110K</td>
                                <td>105K</td>
                                <td className="text-red">-5K</td>
                                <td>
                                    <div className="sentiment-box sent-down">
                                        <i className="fa-solid fa-arrow-trend-down"></i> Negative
                                    </div>
                                </td>
                                <td><span className="status-badge status-pending">Vacant</span></td>
                                <td>
                                    <div className="action-icons">
                                        <button className="btn-icon" title="Edit"><i className="fa-solid fa-pen-to-square"></i></button>
                                        <button className="btn-icon delete" title="Delete"><i className="fa-solid fa-trash-can"></i></button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <Footer />
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;