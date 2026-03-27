import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  clearAuthStorage,
  getStoredDisplayName,
  getStoredUserEmail,
} from '../../services/authService';

// --- HELPER FUNCTION: Auto-generate Initials Avatar ---
const generateInitialsAvatar = (name: string): string => {
  const initials = name
    .split(' ')
    .map((n) => n[0])
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

// Define the User interface
interface User {
  name: string;
  email: string;
  profileUrl?: string | null;
}

const MobileHeader: React.FC = () => {
  const [isHeaderSticky, setIsHeaderSticky] = useState<boolean>(false);
  const location = useLocation();
  const navigate = useNavigate();

  // 1. Set default state to NULL (Logged out by default)
  const [user, setUser] = useState<User | null>(null);

  // 2. Check for actual login token on component mount
  useEffect(() => {
    const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
    const email = getStoredUserEmail();
    const displayName = getStoredDisplayName();
    
    if (token && email) {
      setUser({
        name: displayName || 'User',
        email: email,
        profileUrl: null, // Replace with Google Photo URL when OAuth is implemented
      });
      return;
    }

    setUser(null);
  }, [location.pathname]); // Re-run when navigation happens

  // 3. Handle actual logout
  const handleLogout = () => {
    clearAuthStorage();
    setUser(null);
    navigate("/"); // Send back to home page
  };

  useEffect(() => {
    const handleScroll = () => {
      setIsHeaderSticky(window.scrollY > 90);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // --- REUSABLE AUTH SECTION ---
  const renderAuthSection = () => {
    if (user) {
      return (
        // EXACT SAME HOVER UI AS DESKTOP
        <div className="header-profile profile-hover-container">
          
          <div className="profile-info">
            <span className="user-name" style={{ fontWeight: 600 }}>
              {user.name}
            </span>
            <img 
              src={user.profileUrl || generateInitialsAvatar(user.name)} 
              alt={`${user.name} Profile`} 
              className="user-avatar"
              style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }} 
            />
          </div>

          <div className="logout-action">
            <button 
              onClick={handleLogout} 
              className="btn-outline" 
              // Making the button slightly smaller for mobile fit
              style={{ padding: '6px 16px', fontSize: '13px', cursor: 'pointer', margin: 0 }}
            >
              Logout
            </button>
          </div>

        </div>
      );
    }

    return (
      <div className="auth-buttons" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <Link 
          to="/login" 
          state={{ mode: 'signup', from: location.pathname }} 
          className="btn-outline" 
          style={{ padding: '6px 12px', fontSize: '12px' }}
        >
          Sign Up
        </Link>
        <Link 
          to="/login" 
          state={{ mode: 'login', from: location.pathname }} 
          className="btn-primary" 
          style={{ padding: '6px 14px', fontSize: '12px' }}
        >
          Login
        </Link>
      </div>
    );
  };

  return (
    <>
      {/* SCROLLING FIXED HEADER */}
      <header className={`top-header fixed-header ${isHeaderSticky ? 'visible' : ''}`} id="fixedHeader">
        <Link to="/">
          <img src="/img/logo.png" alt="Reva Logo" className="header-logo" />
        </Link>
        {renderAuthSection()}
      </header>

      {/* MAIN STATIC HEADER */}
      <header className="top-header" id="mainHeader">
        <Link to="/">
          <img src="/img/logo.png" alt="Reva Logo" className="header-logo" />
        </Link>
        {renderAuthSection()}
      </header>
    </>
  );
};

export default MobileHeader;
