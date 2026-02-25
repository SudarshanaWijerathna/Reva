import React, { useEffect, useState } from 'react';

interface DashboardStats {
  total_users: number;
  total_features: number;
  total_predictions: number;
}

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
        
        const response = await fetch('http://localhost:8000/api/admin/stats', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch stats');
        }

        const data = await response.json();
        setStats(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load statistics";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return <div className="dashboard-loading">Loading statistics...</div>;
  }

  if (error) {
    return <div className="dashboard-error">{error}</div>;
  }

  if (!stats) {
    return <div className="dashboard-empty">No data available</div>;
  }

  const statCards = [
    { label: 'Total Users', value: stats.total_users, icon: '👥', color: '--blue-medium' },
    { label: 'Total Features', value: stats.total_features, icon: '⚙️', color: '--blue-medium' },
    { label: 'Total Predictions', value: stats.total_predictions, icon: '📈', color: '--trend-up' }
  ];

  return (
    <div className="admin-dashboard">
      <h2>Dashboard Overview</h2>
      
      <div className="stats-grid">
        {statCards.map((card, index) => (
          <div key={index} className="stat-card">
            <div className="stat-icon">{card.icon}</div>
            <div className="stat-content">
              <p className="stat-label">{card.label}</p>
              <p className="stat-value">{card.value}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-summary">
        <h3>System Status</h3>
        <div className="status-item">
          <span>System Status:</span>
          <span className="status-badge active">Active</span>
        </div>
        <div className="status-item">
          <span>API Connection:</span>
          <span className="status-badge active">Connected</span>
        </div>
        <div className="status-item">
          <span>Database:</span>
          <span className="status-badge active">Healthy</span>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
