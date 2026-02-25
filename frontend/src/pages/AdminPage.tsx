import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import AdminNav from '../components/admin/AdminNav';
import AdminDashboard from '../components/admin/AdminDashboard';
import FeaturesManagement from '../components/admin/FeaturesManagement';
import UsersManagement from '../components/admin/UsersManagement.tsx';
import '../assets/css/admin.css';

type AdminTab = 'dashboard' | 'features' | 'users';

const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState<AdminTab>('dashboard');
  const [isAuthorized, setIsAuthorized] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkAdminAccess = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
        
        if (!token) {
          console.log("No token found, redirecting to login");
          navigate("/login");
          return;
        }

        // Try to fetch admin stats to verify admin access
        const response = await fetch('http://localhost:8000/api/admin/stats', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.status === 403) {
          console.log("User is not admin (403 Forbidden)");
          alert("You don't have admin privileges. Only admin@reva.com can access this panel.");
          navigate("/dashboard");
          return;
        }

        if (!response.ok) {
          throw new Error(`Failed with status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Admin access granted, stats loaded:", data);
        setIsAuthorized(true);
      } catch (err) {
        console.error("Admin access check failed:", err);
        const errorMsg = err instanceof Error ? err.message : "Access check failed";
        console.log("Error details:", errorMsg);
        // Don't redirect on network errors, let user try again
        if (errorMsg.includes("403")) {
          navigate("/login");
        }
      } finally {
        setLoading(false);
      }
    };

    checkAdminAccess();
  }, [navigate]);

  if (loading) {
    return (
      <Layout>
        <div className="admin-loading">
          <div className="spinner"></div>
          <p>Loading Admin Panel...</p>
        </div>
      </Layout>
    );
  }

  if (!isAuthorized) {
    return (
      <Layout>
        <div className="admin-unauthorized">
          <p>Unauthorized Access</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="admin-panel">
        <AdminNav currentTab={currentTab} onTabChange={setCurrentTab} />
        
        <div className="admin-content">
          {currentTab === 'dashboard' && <AdminDashboard />}
          {currentTab === 'features' && <FeaturesManagement />}
          {currentTab === 'users' && <UsersManagement />}
        </div>
      </div>
    </Layout>
  );
};

export default AdminPage;
