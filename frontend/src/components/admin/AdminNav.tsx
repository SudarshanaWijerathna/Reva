import React from 'react';

type AdminTab = 'dashboard' | 'features' | 'models' | 'users';

interface AdminNavProps {
  currentTab: AdminTab;
  onTabChange: (tab: AdminTab) => void;
}

const AdminNav: React.FC<AdminNavProps> = ({ currentTab, onTabChange }) => {
  const tabs: Array<{ id: AdminTab; label: string; icon: string }> = [
    { id: 'dashboard', label: 'Dashboard', icon: '/img/icons/pie_chart.svg' },
    { id: 'features', label: 'Features', icon: '/img/icons/features.svg' },
    { id: 'models', label: 'Models', icon: '/img/icons/models.svg' },
    { id: 'users', label: 'Users', icon: '/img/icons/users.svg' },
  ];

  return (
    <div className="admin-nav">
      {/* Header text placed outside the white card (admin-nav-card) to sit on the page background */}
      <div className="admin-header">
        <h1>Admin Panel</h1>
        <p className="admin-subtitle">Manage features, models, and users</p>
      </div>

      <div className="admin-nav-card">
        <div className="admin-tabs">
          {tabs.map((tab) => (
            <div
              key={tab.id}
              className={`admin-tab ${currentTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onTabChange(tab.id);
                }
              }}
            >
              <div className="tab-icon">
                <img src={tab.icon} alt={tab.label} className="tab-svg-icon" />
              </div>
              <div className="tab-label">{tab.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdminNav;
