import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';
import AddPropertyModal from '../components/AddPropertyModal';
import { portfolioService, type PortfolioSummary, type PropertyData } from '../services/portfolioService';
import '../assets/css/dashboard.css';

// --- HELPER FUNCTION: Auto-generate Initials Avatar ---
const generateInitialsAvatar = (name: string): string => {
  const initials = name
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'U';

  const colors = ['#4445ff', '#00C897', '#fbbf24', '#e11d48', '#9c27b0'];
  const charCode = name.charCodeAt(0) || 0;
  const bgColor = colors[charCode % colors.length];

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <rect width="100" height="100" fill="${bgColor}" />
      <text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-size="40px" font-weight="bold">
        ${initials}
      </text>
    </svg>
  `;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { openAuthModal } = useAuth();

  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [properties, setProperties] = useState<PropertyData[]>([]);
  const [insight, setInsight] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [filter, setFilter] = useState<"all" | "housing" | "rental" | "land">("all");
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingProperty, setEditingProperty] = useState<any>(null);
  const [userName, setUserName] = useState<string>("User");
  const [userProfileUrl, setUserProfileUrl] = useState<string | null>(null);

  const refreshPortfolioData = async () => {
    const [summaryData, propertiesData, insightData] = await Promise.all([
      portfolioService.getSummary(),
      portfolioService.getProperties(),
      portfolioService.getInsights(),
    ]);

    setSummary(summaryData);
    setProperties(propertiesData);
    setInsight(insightData.insight);
  };

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        setLoading(true);
        setError("");

        // Check if user is authenticated using our global localStorage keys
        const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
        const email = localStorage.getItem("user_email") || sessionStorage.getItem("user_email");
        const displayName = localStorage.getItem("user_name") || sessionStorage.getItem("user_name");
        const storedPicture = localStorage.getItem("user_picture") || sessionStorage.getItem("user_picture");

        // FIX: If they are NOT logged in, send to Home and pop the modal with the redirect path!
        if (!token || !email) {
          navigate("/", { replace: true });
          openAuthModal('login', '/dashboard'); // <-- Tells the modal where to go after success
          return;
        }

        setUserName(displayName || (email ? email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1) : 'User'));
        setUserProfileUrl(storedPicture || null);

        await refreshPortfolioData();
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load portfolio data";
        setError(errorMessage);
        console.error("Portfolio data fetch error:", err);

        // FIX: If the backend says the token is expired/unauthorized, force a fresh login modal
        if (errorMessage.includes("Unauthorized")) {
          navigate("/", { replace: true });
          openAuthModal('login', '/dashboard'); // <-- Tells the modal where to go after success
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, [navigate, location.pathname, openAuthModal]);

  // Handle property added callback
  const handlePropertyAdded = async () => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    try {
      await refreshPortfolioData();
    } catch (err) {
      console.error("Failed to refresh portfolio data:", err);
    }
  };

  const handleEditProperty = async (property: PropertyData) => {
    try {
      const detail = await portfolioService.getPropertyDetails(property.property_id);
      setEditingProperty(detail);
      setIsAddModalOpen(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load property details';
      setError(errorMessage);
    }
  };

  const handleDeleteProperty = async (property: PropertyData) => {
    const confirmed = window.confirm(`Delete this ${property.type} property? This cannot be undone.`);
    if (!confirmed) {
      return;
    }

    try {
      await portfolioService.deleteProperty(property.property_id, property.type);
      await refreshPortfolioData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete property';
      setError(errorMessage);
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
    if (lower.includes("high") || lower.includes("positive") || lower.includes("bullish")) return "sent-up";
    if (lower.includes("negative") || lower.includes("bearish")) return "sent-down";
    return "sent-neutral";
  };

  // Get sentiment trend icon
  const getSentimentIcon = (sentiment: string): string => {
    const lower = sentiment.toLowerCase();
    if (lower.includes("high") || lower.includes("positive") || lower.includes("bullish")) return "fa-arrow-trend-up";
    if (lower.includes("negative") || lower.includes("bearish")) return "fa-arrow-trend-down";
    return "fa-minus";
  };

  return (
    <Layout>
      <div className="dashboard-wrapper">

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

        <div className="portfolio-summary-section">
          {/* HEADER */}
          <div className="dash-header">
            <div className="header-left-group">
              <img
                src={userProfileUrl || generateInitialsAvatar(userName)}
                alt="User Profile"
                className="dash-user-avatar"
              />
              <div className="header-text-group">
                <h1> <span>{userName}'s Portfolio</span> </h1>
                <p>Track your real estate assets and monitor market value changes.</p>
              </div>
            </div>
            <div className="header-actions-group">
              <div className="horizontal-mix-stats">
                <div className="mix-stat-item">
                  <i className="fa-solid fa-house"></i>
                  <span>Housing:</span>
                  <strong>{loading ? "..." : (summary?.property_mix.housing || 0) > 0 ? `${summary?.property_mix.housing} Units` : "-"}</strong>
                </div>
                <div className="mix-stat-item">
                  <i className="fa-solid fa-building"></i>
                  <span>Rentals:</span>
                  <strong>{loading ? "..." : (summary?.property_mix.rental || 0) > 0 ? `${summary?.property_mix.rental} Units` : "-"}</strong>
                </div>
                <div className="mix-stat-item">
                  <i className="fa-solid fa-tree"></i>
                  <span>Lands:</span>
                  <strong>{loading ? "..." : (summary?.property_mix.land || 0) > 0 ? `${summary?.property_mix.land} Plots` : "-"}</strong>
                </div>
              </div>
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="btn-primary"
                title="Add a new property to track and analyze"
              >
                <i className="fa-solid fa-plus"></i> New Property
              </button>
            </div>
          </div>

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
          </div>
        </div>

        <div className="main-content">

          {/* INSIGHT SECTION */}
          <div className="insight-row">
            <div className="insight-card">
              <div className="insight-header">
                <i className="fa-solid fa-robot"></i>
                <h4>Reva Insight</h4>
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
                <span className="card-subtitle"><i className="fa-solid fa-circle-info"></i> Valuations estimated using Reva ML models (Data: Oct 2025)</span>
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

            <div className="properties-container">
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
                <>
                  {/* Desktop Table View */}
                  <div className="table-responsive desktop-only-view">
                    <table className="reva-table">
                      <thead>
                        <tr>
                          <th>Listed Date</th>
                          <th>Type</th>
                          <th>Location</th>
                          <th>Bought Price</th>
                          <th>Current Val <i className="fa-solid fa-circle-info info-icon" title="Predicted by Reva AI"></i></th>
                          <th>Profit</th>
                          <th>Sentiment</th>
                          <th>Status</th>
                          <th style={{ textAlign: 'right' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredProperties.map((property) => (
                          <tr key={property.property_id}>
                            <td>{formatDate(property.created_at)}</td>
                            <td>
                              <i className={`fa-solid ${property.type === "housing" ? "fa-house" :
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
                                <button className="btn-icon" title="Edit" onClick={() => handleEditProperty(property)}><i className="fa-solid fa-pen-to-square"></i></button>
                                <button className="btn-icon delete" title="Delete" onClick={() => handleDeleteProperty(property)}><i className="fa-solid fa-trash-can"></i></button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Mobile Card View */}
                  <div className="property-cards-mobile mobile-only-view">
                    {filteredProperties.map((property) => (
                      <div key={property.property_id} className="property-card-item">
                        {/* Header Row: Location, Type and Status */}
                        <div className="property-card-header">
                          <div className="property-card-title-group">
                            <div className="property-card-location">{property.location}</div>
                            <div className="property-card-type">
                              <i className={`fa-solid ${property.type === "housing" ? "fa-house" :
                                property.type === "rental" ? "fa-building" :
                                  "fa-tree"
                                } type-icon`}></i>
                              {property.type.charAt(0).toUpperCase() + property.type.slice(1)}
                            </div>
                          </div>
                          <span className={`status-badge status-${property.status.toLowerCase()}`}>
                            {property.status}
                          </span>
                        </div>

                        {/* Body Details */}
                        <div className="property-card-body">
                          <div className="property-card-row">
                            <span className="property-card-label">Listed Date:</span>
                            <span>{formatDate(property.created_at)}</span>
                          </div>
                          <div className="property-card-row">
                            <span className="property-card-label">Bought Price:</span>
                            <strong className="price-value">{formatCurrency(property.purchase_price)}</strong>
                          </div>
                          <div className="property-card-row">
                            <span className="property-card-label">Current Val:</span>
                            <strong className="price-value current-val-text">{formatCurrency(property.current_value)}</strong>
                          </div>
                          <div className="property-card-row">
                            <span className="property-card-label">Profit:</span>
                            <span className={property.profit >= 0 ? "text-green" : "text-red"}>
                              <strong>{property.profit >= 0 ? "+" : ""}{formatCurrency(property.profit)}</strong>
                            </span>
                          </div>
                          <div className="property-card-row align-center">
                            <span className="property-card-label">Sentiment:</span>
                            <div className={`sentiment-box ${getSentimentClass(property.sentiment)}`}>
                              <i className={`fa-solid ${getSentimentIcon(property.sentiment)}`}></i>
                              {property.sentiment.charAt(0).toUpperCase() + property.sentiment.slice(1)}
                            </div>
                          </div>
                        </div>

                        {/* Footer Action Icons */}
                        <div className="property-card-actions">
                          <div className="property-card-actions-left">
                            <button className="btn-icon" title="Edit" onClick={() => handleEditProperty(property)}><i className="fa-solid fa-pen-to-square"></i></button>
                          </div>
                          <div className="property-card-actions-right">
                            <button className="btn-icon delete" title="Delete" onClick={() => handleDeleteProperty(property)}><i className="fa-solid fa-trash-can"></i></button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Add Property Modal */}
      <AddPropertyModal
        isOpen={isAddModalOpen}
        onClose={() => {
          setIsAddModalOpen(false);
          setEditingProperty(null);
        }}
        onPropertyAdded={handlePropertyAdded}
        initialProperty={editingProperty}
      />
    </Layout>
  );
};

export default Dashboard;