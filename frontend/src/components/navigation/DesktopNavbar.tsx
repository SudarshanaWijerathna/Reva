import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import '../../assets/css/navbar.css';

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
  const [isSticky, setIsSticky] = useState<boolean>(false);
  const location = useLocation();
  const navigate = useNavigate();

  // 1. Set default state to NULL (Logged out by default)
  const [user, setUser] = useState<User | null>(null);

  // 2. Check for actual login token on component mount
  useEffect(() => {
    const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
    const email = localStorage.getItem("user_email") || sessionStorage.getItem("user_email");
    
    if (token && email) {
      // Create a display name from the email (e.g., admin@reva.com -> "Admin")
      const displayName = email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1);
      setUser({
        name: displayName,
        email: email,
        profileUrl: null, // Replace with Google Photo URL when OAuth is implemented
      });
    }
  }, [location.pathname]); // Re-run when navigation happens

  // 3. Handle actual logout
  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("user_email");
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("token_type");
    sessionStorage.removeItem("user_email");
    setUser(null);
    navigate("/"); // Send back to home page
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
          <li className={isActive('/askreva')}><Link to="/askreva" state={{ from: location.pathname }}>Ask Reva</Link></li>
          <li className={isActive('/support')}><Link to="/support">Support</Link></li>

        </ul>

        <div className="nav-actions">
          {user ? (
            // LOGGED IN VIEW: Profile Hover Swap Container
            <div className="header-profile profile-hover-container">
              
              <div className="profile-info">
                <span className="user-name" style={{ fontWeight: 600 }}>
                  {user.name.split(' ')[0]} {/* Strictly one word */}
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
            // LOGGED OUT VIEW: Wrapped in a div to prevent flexbox button stretching
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
