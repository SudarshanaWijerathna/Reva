import React from 'react';

interface AdminNavProps {
  currentTab: 'dashboard' | 'features' | 'models' | 'users';
  onTabChange: (tab: 'dashboard' | 'features' | 'models' | 'users') => void;
}

const AdminNav: React.FC<AdminNavProps> = ({ currentTab, onTabChange }) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'features', label: 'Features', icon: '⚙️' },
    { id: 'models', label: 'Models', icon: '🧠' },
    { id: 'users', label: 'Users', icon: '👥' }
  ];

  return (
    <div className="admin-nav">
      <div className="admin-header">
        <h1>Admin Panel</h1>
        <p className="admin-subtitle">Manage features and users</p>
      </div>
      
      <div className="admin-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`admin-tab ${currentTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id as any)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AdminNav;
