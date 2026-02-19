import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import Footer from '../components/Footer';
import AddPropertyModal from '../components/AddPropertyModal';
import { portfolioService, type PortfolioSummary, type PropertyData } from '../services/portfolioService';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [properties, setProperties] = useState<PropertyData[]>([]);
  const [insight, setInsight] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [filter, setFilter] = useState<"all" | "housing" | "rental" | "land">("all");
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        setLoading(true);
        setError("");

        // Check if user is authenticated
        const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
        if (!token) {
          navigate("/login");
          return;
        }

        // Fetch all portfolio data in parallel
        const [summaryData, propertiesData, insightData] = await Promise.all([
          portfolioService.getSummary(),
          portfolioService.getProperties(),
          portfolioService.getInsights(),
        ]);

        setSummary(summaryData);
        setProperties(propertiesData);
        setInsight(insightData.insight);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load portfolio data";
        setError(errorMessage);
        console.error("Portfolio data fetch error:", err);

        // If unauthorized, redirect to login
        if (errorMessage.includes("Unauthorized")) {
          navigate("/login");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, [navigate]);

  // Handle property added callback
  const handlePropertyAdded = async () => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    try {
      const [summaryData, propertiesData] = await Promise.all([
        portfolioService.getSummary(),
        portfolioService.getProperties(),
      ]);
      setSummary(summaryData);
      setProperties(propertiesData);
    } catch (err) {
      console.error("Failed to refresh portfolio data:", err);
    }
  };

  // Filter properties based on selected type
  const filteredProperties = properties.filter(
    (prop) => filter === "all" || prop.type === filter
  );

  // Format currency - handle undefined/zero values
  const formatCurrency = (value: number | undefined): string => {
    if (value === undefined || value === null || value === 0) {
      return "-";
    }
    if (value >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(1)}M`;
    }
    if (value >= 1_000) {
      return `${(value / 1_000).toFixed(1)}K`;
    }
    return value.toFixed(0);
  };

  // Format date
  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  // Get sentiment badge styling
  const getSentimentClass = (sentiment: string): string => {
    const lower = sentiment.toLowerCase();
    if (lower.includes("high") || lower.includes("positive")) return "sent-up";
    if (lower.includes("negative")) return "sent-down";
    return "sent-neutral";
  };

  // Get sentiment trend icon
  const getSentimentIcon = (sentiment: string): string => {
    const lower = sentiment.toLowerCase();
    if (lower.includes("high") || lower.includes("positive")) return "fa-arrow-trend-up";
    if (lower.includes("negative")) return "fa-arrow-trend-down";
    return "fa-minus";
  };

  return (
    <Layout>
      <div className="dashboard-wrapper">
        
        {/* HEADER */}
        <div className="dash-header">
            <div>
                <h1>My Property Portfolio</h1>
                <p>Track your real estate assets and monitor market value changes.</p>
            </div>
            <button 
              onClick={() => setIsAddModalOpen(true)}
              className="btn-primary" 
              title="Add a new property to track and analyze"
            >
                <i className="fa-solid fa-plus"></i> New Property
            </button>
        </div>

        {/* ERROR MESSAGE */}
        {error && (
          <div style={{
            padding: "12px 16px",
            backgroundColor: "#fce8e6",
            color: "#d93025",
            borderRadius: "8px",
            marginBottom: "24px",
            display: "flex",
            alignItems: "center",
            gap: "12px"
          }}>
            <i className="fa-solid fa-exclamation-circle"></i>
            <span>{error}</span>
          </div>
        )}

        <div className="main-content">
            
            {/* FINANCIAL GRID */}
            <div className="financial-grid">
                <div className="fin-card">
                    <div className="fin-label"><i className="fa-solid fa-sack-dollar"></i> Portfolio Value</div>
                    <div className="fin-value">
                      {loading ? "..." : summary ? formatCurrency(summary.portfolio_value) : "-"}
                    </div>
                    <div className="fin-sub text-green">
                      <i className="fa-solid fa-arrow-trend-up"></i>
                      {loading ? "Loading..." : summary && summary.portfolio_value > 0 ? `+${summary.growth_percentage}% overall` : "-"}
                    </div>
                </div>
                
                <div className="fin-card">
                    <div className="fin-label"><i className="fa-solid fa-hand-holding-dollar"></i> Total Profit</div>
                    <div className="fin-value">
                      {loading ? "..." : summary ? formatCurrency(summary.total_profit) : "-"}
                    </div>
                    <div className="fin-sub text-green">Unrealized gains</div>
                </div>
                
                <div className="fin-card">
                    <div className="fin-label"><i className="fa-regular fa-face-smile"></i> Sentiment</div>
                    <div className="fin-value">
                      {loading ? "Loading..." : summary?.sentiment || "-"}
                    </div>
                    <div className="fin-sub text-green">Market looks {summary?.sentiment?.toLowerCase() || "neutral"}</div>
                </div>

                <div className="fin-card">
                    <div className="fin-label"><i className="fa-solid fa-layer-group"></i> Property Mix</div>
                    <ul className="prop-mix-list">
                        <li className="prop-mix-item">
                            <span><i className="fa-solid fa-house"></i> Housing</span>
                            <strong>{loading ? "..." : (summary?.property_mix.housing || 0) > 0 ? summary?.property_mix.housing : "-"} {(summary?.property_mix.housing || 0) > 0 ? "Units" : ""}</strong>
                        </li>
                        <li className="prop-mix-item">
                            <span><i className="fa-solid fa-building"></i> Rentals</span>
                            <strong>{loading ? "..." : (summary?.property_mix.rental || 0) > 0 ? summary?.property_mix.rental : "-"} {(summary?.property_mix.rental || 0) > 0 ? "Units" : ""}</strong>
                        </li>
                        <li className="prop-mix-item">
                            <span><i className="fa-solid fa-tree"></i> Lands</span>
                            <strong>{loading ? "..." : (summary?.property_mix.land || 0) > 0 ? summary?.property_mix.land : "-"} {(summary?.property_mix.land || 0) > 0 ? "Plots" : ""}</strong>
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
                        {loading ? "Loading insights..." : insight || "No insights available at the moment."}
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
                    
                    <select 
                      className="dashboard-filter"
                      value={filter}
                      onChange={(e) => setFilter(e.target.value as any)}
                    >
                        <option value="all">View All</option>
                        <option value="housing">Housing</option>
                        <option value="rental">Rental</option>
                        <option value="land">Land</option>
                    </select>
                </div>

                <div className="table-responsive">
                    {loading ? (
                      <div style={{ padding: "32px", textAlign: "center", color: "#666" }}>
                        <i className="fa-solid fa-spinner fa-spin" style={{ marginRight: "8px" }}></i>
                        Loading properties...
                      </div>
                    ) : filteredProperties.length === 0 ? (
                      <div style={{ padding: "32px", textAlign: "center", color: "#999" }}>
                        <p>No properties found</p>
                      </div>
                    ) : (
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
                            {filteredProperties.map((property) => (
                              <tr key={property.property_id}>
                                <td>{formatDate(property.created_at)}</td>
                                <td>
                                  <i className={`fa-solid ${
                                    property.type === "housing" ? "fa-house" :
                                    property.type === "rental" ? "fa-building" :
                                    "fa-tree"
                                  } type-icon`}></i>
                                  {property.type.charAt(0).toUpperCase() + property.type.slice(1)}
                                </td>
                                <td>{property.location}</td>
                                <td>{formatCurrency(property.purchase_price)}</td>
                                <td>{formatCurrency(property.current_value)}</td>
                                <td className={property.profit >= 0 ? "text-green" : "text-red"}>
                                  {property.profit >= 0 ? "+" : ""}{formatCurrency(property.profit)}
                                </td>
                                <td>
                                    <div className={`sentiment-box ${getSentimentClass(property.sentiment)}`}>
                                        <i className={`fa-solid ${getSentimentIcon(property.sentiment)}`}></i>
                                        {property.sentiment.charAt(0).toUpperCase() + property.sentiment.slice(1)}
                                    </div>
                                </td>
                                <td>
                                  <span className={`status-badge status-${property.status.toLowerCase()}`}>
                                    {property.status}
                                  </span>
                                </td>
                                <td>
                                    <div className="action-icons">
                                        <button className="btn-icon" title="Edit"><i className="fa-solid fa-pen-to-square"></i></button>
                                        <button className="btn-icon delete" title="Delete"><i className="fa-solid fa-trash-can"></i></button>
                                    </div>
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    )}
                </div>
            </div>

            <Footer />
        </div>
      </div>

      {/* Add Property Modal */}
      <AddPropertyModal 
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onPropertyAdded={handlePropertyAdded}
      />
    </Layout>
  );
};

export default Dashboard;