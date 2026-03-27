import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
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

const MobileHeader: React.FC = () => {
  const { openAuthModal, authUpdateKey } = useAuth(); 

  const [isHeaderSticky, setIsHeaderSticky] = useState<boolean>(false);
  const location = useLocation();

  const [user, setUser] = useState<User | null>(null);
  const [showLogout, setShowLogout] = useState<boolean>(false);

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

  // --- BULLETPROOF LOGOUT ---
  const handleLogout = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation(); // Prevents the click from bubbling and confusing React
    }
    
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
    
    // Physically force the browser back to the homepage to guarantee a clean state reset
    window.location.href = "/"; 
  };

  // --- NEW: Smart Click-Outside & Scroll Detector ---
  useEffect(() => {
    // 1. Close if they click anywhere outside the profile area
    const handleClickOutside = (e: MouseEvent) => {
      if (!(e.target as Element).closest('.mobile-auth-container')) {
        setShowLogout(false);
      }
    };

    // 2. Close if they start scrolling the page
    const handleScroll = () => {
      setIsHeaderSticky(window.scrollY > 90);
      setShowLogout(false); // Auto-hide menu on scroll!
    };

    window.addEventListener('scroll', handleScroll);

    if (showLogout) {
      // Small delay prevents the opening click from immediately triggering the closing listener
      setTimeout(() => document.addEventListener('click', handleClickOutside), 10);
    }

    return () => {
      window.removeEventListener('scroll', handleScroll);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showLogout]);

  const renderAuthSection = () => {
    if (user) {
      return (
        // Added the class 'mobile-auth-container' so our smart click detector knows what to look for
        <div className="mobile-auth-container" style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          
          {/* Inline Logout Button (Slides out smoothly to the left) */}
          <div style={{
            position: 'absolute',
            right: '100%', 
            marginRight: '12px', 
            opacity: showLogout ? 1 : 0,
            visibility: showLogout ? 'visible' : 'hidden',
            transform: showLogout ? 'translateX(0)' : 'translateX(10px)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)', // Snappier animation
            pointerEvents: showLogout ? 'auto' : 'none', 
            zIndex: 999
          }}>
            <button 
              onClick={handleLogout} 
              className="btn-outline" 
              style={{ 
                padding: '6px 16px', 
                fontSize: '13px', 
                cursor: 'pointer', 
                margin: 0, 
                whiteSpace: 'nowrap', 
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)', // Subtle shadow
                backgroundColor: '#ffffff00' // Ensures it blocks any background elements
              }}
            >
              Logout
            </button>
          </div>
          
          {/* The Clickable Profile Trigger */}
          <div 
            onClick={(e) => {
              e.stopPropagation();
              setShowLogout(!showLogout);
            }}
            style={{ 
              cursor: 'pointer', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              position: 'relative',
              zIndex: 999 
            }}
          >
            <span style={{ fontWeight: 600, fontSize: '14px', color: '#000020' }}>
              {user.name.split(' ')[0]} 
            </span>
            <img 
              src={user.profileUrl || generateInitialsAvatar(user.name)} 
              alt={`${user.name} Profile`} 
              style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover' }} 
            />
          </div>

        </div>
      );
    }

    return (
      <div className="auth-buttons" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <button 
          onClick={() => openAuthModal('signup')} 
          className="btn-outline" 
          style={{ 
            padding: '0 16px', 
            fontSize: '13px',
            height: '36px',
            boxSizing: 'border-box',
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            lineHeight: 1
          }}
        >
          Sign Up
        </button>
        <button 
          onClick={() => openAuthModal('login')} 
          className="btn-primary" 
          style={{ 
            padding: '0 16px', 
            fontSize: '13px', 
            height: '36px', 
            boxSizing: 'border-box', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            border: '1px solid transparent', 
            lineHeight: 1
          }}
        >
          Login
        </button>
      </div>
    );
  };

  return (
    <>
      <header className={`top-header fixed-header ${isHeaderSticky ? 'visible' : ''}`} id="fixedHeader">
        <Link to="/">
          <img src="/img/logo.png" alt="Reva Logo" className="header-logo" />
        </Link>
        {renderAuthSection()}
      </header>

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