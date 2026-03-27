import React from 'react';

type AdminTab = 'dashboard' | 'features' | 'models' | 'users';

interface AdminNavProps {
  currentTab: AdminTab;
  onTabChange: (tab: AdminTab) => void;
}

const AdminNav: React.FC<AdminNavProps> = ({ currentTab, onTabChange }) => {
  const tabs: Array<{ id: AdminTab; label: string; icon: string }> = [
    { id: 'dashboard', label: 'Dashboard', icon: 'fa-chart-pie' },
    { id: 'features', label: 'Features', icon: 'fa-sliders' },
    { id: 'models', label: 'Models', icon: 'fa-brain' },
    { id: 'users', label: 'Users', icon: 'fa-users' },
  ];

  return (
    <div className="admin-nav">
      <div className="admin-header">
        <h1>Admin Panel</h1>
        <p className="admin-subtitle">Manage features, models, and users</p>
      </div>

      <div className="admin-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`admin-tab ${currentTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="tab-icon">
              <i className={`fa-solid ${tab.icon}`}></i>
            </span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AdminNav;
