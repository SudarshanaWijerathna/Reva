import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const DesktopNavbar: React.FC = () => {
  const [isSticky, setIsSticky] = useState<boolean>(false);
  const location = useLocation();

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
          <li className={isActive('/contact')}><Link to="/contact">Ask Reva</Link></li>
          <li className={isActive('/support')}><Link to="/support">Support</Link></li>
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