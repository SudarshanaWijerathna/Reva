import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

const DesktopNavbar: React.FC = () => {
  const [isSticky, setIsSticky] = useState<boolean>(false);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const location = useLocation();
  const navigate = useNavigate();

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

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
      if (token) {
        setIsLoggedIn(true);
        try {
          const response = await fetch('http://localhost:8000/api/admin/stats', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });
          if (response.ok) setIsAdmin(true);
        } catch (err) {
          console.log('User is not admin');
        }
      }
    };
    checkAuth();
  }, [location]);

  const isActive = (path: string): string => location.pathname === path ? 'selected' : '';
  const isPrediction = location.pathname.includes('price');
  
  const handleLogout = () => {
    localStorage.removeItem("access_token");
    sessionStorage.removeItem("access_token");
    setIsLoggedIn(false);
    setIsAdmin(false);
    navigate("/login");
  };

  return (
    <nav className={`navbar ${isSticky ? 'sticky' : ''}`} id="desktopNavbar">
      <div className="nav-container">
        <div className="nav-brand">
          <Link to="/">
             <img src="/src/assets/logo.png" alt="Reva Logo" className="header-logo" style={{ height: '35px' }} />
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
          <li className={isActive('/contact')}><Link to="/contact">Ask Reva</Link></li>
          <li className={isActive('/support')}><Link to="/support">Support</Link></li>
          {isAdmin && <li className={isActive('/admin')}><Link to="/admin">Admin</Link></li>}
        </ul>

        <div className="nav-actions header-profile">
            <span className="user-name">Isuru Sudarshana</span>
            <img src="https://i.pravatar.cc/150?img=11" alt="Profile" className="user-avatar" />
        </div>
      </div>
    </nav>
  );
};

export default DesktopNavbar;