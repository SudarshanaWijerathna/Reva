import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import '../../assets/css/navbar.css';
import {
  clearAuthStorage,
  getStoredDisplayName,
  getStoredUserEmail,
  isStoredAdmin,
} from '../../services/authService';

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

interface User {
  name: string;
  email: string;
  profileUrl?: string | null;
}

const DesktopNavbar: React.FC = () => {
  const [isSticky, setIsSticky] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const isAdmin = isStoredAdmin();

  useEffect(() => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const email = getStoredUserEmail();
    const displayName = getStoredDisplayName();

    if (token && email) {
      setUser({
        name: displayName || 'User',
        email,
        profileUrl: null,
      });
      return;
    }

    setUser(null);
  }, [location.pathname]);

  useEffect(() => {
    let scrollTimeout: ReturnType<typeof setTimeout> | null = null;

    const handleScroll = () => {
      if (scrollTimeout) return;
      scrollTimeout = setTimeout(() => {
        setIsSticky(window.scrollY > 300);
        scrollTimeout = null;
      }, 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogout = () => {
    clearAuthStorage();
    setUser(null);
    navigate('/');
  };

  const isActive = (path: string): string => (location.pathname === path ? 'selected' : '');
  const isPrediction = location.pathname.includes('price');
  const isSupport = location.pathname === '/support' || location.pathname === '/contact';
  const isAskReva = location.pathname === '/askreva';
  const isAdminPage = location.pathname === '/admin';

  return (
    <nav className={`navbar ${isSticky ? 'sticky' : ''}`} id="mainNavbar">
      <div className="nav-container">
        <div className="nav-brand">
          <Link to="/">
            <img src="/img/logo.png" alt="Reva Logo" className="header-logo" style={{ height: '35px' }} />
          </Link>
        </div>

        <ul className="nav-links">
          <li className={isActive('/')}><Link to="/">Home</Link></li>
          <li className={isActive('/dashboard')}><Link to="/dashboard">Dashboard</Link></li>
          <li className={`d-nav-item-container ${isPrediction ? 'selected' : ''}`}>
            <Link to="#">Prediction <i className="fa-solid fa-chevron-down" style={{ fontSize: '10px' }}></i></Link>
            <div className="d-prediction-popup">
              <Link to="/house-price">House price prediction</Link>
              <Link to="/rental-price">Rental price prediction</Link>
              <Link to="/land-price">Land price prediction</Link>
            </div>
          </li>
          <li className={isSupport ? 'selected' : ''}><Link to="/support">Support</Link></li>
          <li className={isAskReva ? 'selected' : ''}><Link to="/askreva" state={{ from: location.pathname }}>Ask Reva</Link></li>
          {isAdmin && <li className={isAdminPage ? 'selected' : ''}><Link to="/admin">Admin</Link></li>}
        </ul>

        <div className="nav-actions">
          {user ? (
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
                  style={{ padding: '6px 20px', fontSize: '14px', cursor: 'pointer', margin: 0 }}
                >
                  Logout
                </button>
              </div>
            </div>
          ) : (
            <div className="auth-buttons" style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <Link to="/login" state={{ mode: 'signup', from: location.pathname }} className="btn-outline">
                Sign Up
              </Link>
              <Link to="/login" state={{ mode: 'login', from: location.pathname }} className="btn-primary">
                Login
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default DesktopNavbar;
