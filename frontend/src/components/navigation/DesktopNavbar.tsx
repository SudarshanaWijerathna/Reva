import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../../assets/css/navbar.css';
import { useAuth } from '../../context/AuthContext';

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

interface User {
  name: string;
  email: string;
  profileUrl?: string | null;
}

const DesktopNavbar: React.FC = () => {
  const { openAuthModal, authUpdateKey } = useAuth(); 
  
  const [isSticky, setIsSticky] = useState<boolean>(false);
  const location = useLocation();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
    const email = localStorage.getItem("user_email") || sessionStorage.getItem("user_email");
    const storedName = localStorage.getItem("user_name") || sessionStorage.getItem("user_name");
    const storedPicture = localStorage.getItem("user_picture") || sessionStorage.getItem("user_picture");
    
    if (token && (email || storedName)) {
      const displayName = storedName || (email ? email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1) : "User");
      setUser({
        name: displayName,
        email: email || "",
        profileUrl: storedPicture || null, 
      });
    }
  }, [location.pathname, authUpdateKey]); 

  // --- THE FIX: Bulletproof Hard Logout ---
  const handleLogout = (e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user_email");
    localStorage.removeItem("user_name");    
    localStorage.removeItem("user_picture"); 
    localStorage.removeItem("reva_backup_name");
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("token_type");
    sessionStorage.removeItem("user_email");
    sessionStorage.removeItem("user_name");    
    sessionStorage.removeItem("user_picture"); 
    
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

  const isActive = (path: string): string => location.pathname === path ? 'selected' : '';
  const isPrediction = location.pathname.includes('price');

  const handleProtectedNavigation = (e: React.MouseEvent) => {
    const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
    if (!token) {
      e.preventDefault(); 
      openAuthModal('login', '/dashboard'); 
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
          
          <li className={`d-nav-item-container ${isPrediction ? 'selected' : ''}`}>
             <Link to="#">Prediction <i className="fa-solid fa-chevron-down" style={{ fontSize: '10px' }}></i></Link>
             <div className="d-prediction-popup">
                 <Link to="/house-price">House price prediction</Link>
                 <Link to="/rental-price">Rental price prediction</Link>
                 <Link to="/land-price">Land price prediction</Link>
             </div>
          </li>
          <li className={isActive('/askreva')}><Link to="/askreva" state={{ from: location.pathname }}>Ask Reva</Link></li>
          <li className={isActive('/support')}><Link to="/support">Support</Link></li>
        </ul>

        <div className="nav-actions">
          {user ? (
            <div className="header-profile profile-hover-container">
              
              <div className="profile-info">
                <span className="user-name" style={{ fontWeight: 600 }}>
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