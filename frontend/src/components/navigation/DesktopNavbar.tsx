import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../../assets/css/navbar.css';
import { useAuth } from '../../context/AuthContext';
import ThemeIcon from '../common/ThemeIcon';
import {
  clearAuthStorage,
  getStoredDisplayName,
  getStoredUserEmail,
  isStoredAdmin,
} from '../../services/authService';

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

interface User {
  name: string;
  email: string;
  profileUrl?: string | null;
}

const DesktopNavbar: React.FC = () => {
  const { openAuthModal, authUpdateKey } = useAuth(); 
  const location = useLocation();
  
  const [isSticky, setIsSticky] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);

  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme !== null) {
      return savedTheme === 'dark';
    }
    return true; // Default to dark theme
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  // Check admin status from the auth service only if authenticated
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  const isAdmin = !!token && isStoredAdmin();

  // --- MERGED: Uses authService helpers but retains authUpdateKey dependency ---
  useEffect(() => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const email = getStoredUserEmail();
    const displayName = getStoredDisplayName();
    const storedPicture = localStorage.getItem("user_picture") || sessionStorage.getItem("user_picture");

    if (token && (email || displayName)) {
      setUser({
        name: displayName || (email ? email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1) : 'User'),
        email: email || '',
        profileUrl: storedPicture || null,
      });
    } else {
      setUser(null);
    }
  }, [location.pathname, authUpdateKey]); 

  // --- MERGED: Uses authService to clear, but retains the bulletproof hard redirect ---
  const handleLogout = (e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    
    // Clear via the incoming service
    clearAuthStorage();
    // Manually clear our fallback from the signup logic just in case
    localStorage.removeItem("reva_backup_name");
    
    // Physically force the browser back to the homepage
    window.location.href = "/"; 
  };

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

  const isActive = (path: string): string => (location.pathname === path ? 'selected' : '');
  const isPrediction = location.pathname.includes('price');
  const isSupport = location.pathname === '/support' || location.pathname === '/contact';
  const isAskReva = location.pathname === '/askreva';
  const isAdminPage = location.pathname === '/admin';

  // --- MERGED: Retains the modal interceptor logic ---
  const handleProtectedNavigation = (e: React.MouseEvent) => {
    const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
    if (!token) {
      e.preventDefault(); 
      openAuthModal('login', '/dashboard'); 
    }
  };

  const handleProtectedAskRevaNavigation = (e: React.MouseEvent) => {
    const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
    if (!token) {
      e.preventDefault(); 
      openAuthModal('login', '/askreva'); 
    }
  };

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
          
          <li className={isActive('/dashboard')}>
            <Link to="/dashboard" onClick={handleProtectedNavigation}>Dashboard</Link>
          </li>
          
          <li className={isPrediction ? 'selected' : ''}>
            <Link to="/house-price">Prediction</Link>
          </li>
          
          {/* --- MERGED: Retains specific active states and conditional Admin link --- */}
          <li className={isSupport ? 'selected' : ''}><Link to="/support">Support</Link></li>
          <li className={isAskReva ? 'selected' : ''}>
            <Link to="/askreva" state={{ from: location.pathname }} onClick={handleProtectedAskRevaNavigation}>Ask Reva</Link>
          </li>
          {isAdmin && <li className={isAdminPage ? 'selected' : ''}><Link to="/admin">Admin</Link></li>}
        </ul>

        <div className="nav-actions">
          <button 
            onClick={toggleDarkMode} 
            className="dark-mode-btn" 
            aria-label="Toggle dark mode"
            title="Toggle theme"
          >
            <ThemeIcon darkMode={darkMode} size={18} />
          </button>
          {user ? (
            <div className="header-profile profile-hover-container">
              <div className="profile-info">
                <span
                  className="user-name"
                  style={{
                    fontWeight: 600,
                    maxWidth: '120px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    display: 'inline-block',
                    verticalAlign: 'middle',
                  }}
                  title={user.name}
                >
                  {user.name.split(' ')[0]} 
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
              <button onClick={() => openAuthModal('signup')} className="btn-outline">
                Sign Up
              </button>
              <button onClick={() => openAuthModal('login')} className="btn-primary">
                Login
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default DesktopNavbar;