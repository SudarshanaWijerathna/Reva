import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext'; // --- ADDED: Import AuthContext ---

const MobileBottomNav: React.FC = () => {
  const { openAuthModal } = useAuth(); // --- ADDED: hook ---
  const [isPredictionPopupOpen, setIsPredictionPopupOpen] = useState<boolean>(false);
  const location = useLocation();

  const isActive = (path: string): string => location.pathname === path ? 'active' : '';

  // --- ADDED: Intercept clicks for protected mobile routes ---
  const handleProtectedNavigation = (e: React.MouseEvent) => {
    const token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token");
    if (!token) {
      e.preventDefault(); 
      openAuthModal('login', '/dashboard'); // Trigger popup and remember where to go!
    }
  };

  return (
    <nav className="bottom-nav">
      
      {/* Overlay for Popup - Notice it is inside the nav tag to match index.html exactly */}
      <div 
        className={`popup-overlay ${isPredictionPopupOpen ? 'show' : ''}`} 
        id="popupOverlay"
        onClick={() => setIsPredictionPopupOpen(false)}
      ></div>

      <Link to="/support" className={`nav-item ${isActive('/support')}`}>
        <img src="/img/icons/support.svg" alt="Support" className="nav-icon" />
        <span className="nav-text">Support</span>
      </Link>
      
      <div className="nav-item-container">
        <button 
          className={`nav-item ${location.pathname.includes('price') ? 'active' : ''}`} 
          id="predictionToggle"
          onClick={(e) => {
            e.preventDefault();
            setIsPredictionPopupOpen(!isPredictionPopupOpen);
          }}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
          <img src="/img/icons/prediction.svg" alt="Prediction" className="nav-icon" />
          <span className="nav-text">Prediction</span>
        </button>
        
        {/* Prediction Popup Menu */}
        <div className={`prediction-popup ${isPredictionPopupOpen ? 'show' : ''}`} id="predictionPopup">
          <Link to="/house-price" className="popup-item" onClick={() => setIsPredictionPopupOpen(false)}>
            <div className="popup-icon-circle"><img src="/img/icons/house.svg" alt="House" /></div>
            <div className="popup-label">House price prediction</div>
          </Link>
          <Link to="/rental-price" className="popup-item" onClick={() => setIsPredictionPopupOpen(false)}>
            <div className="popup-icon-circle"><img src="/img/icons/rental.svg" alt="Rental" /></div>
            <div className="popup-label">Rental price prediction</div>
          </Link>
          <Link to="/land-price" className="popup-item" onClick={() => setIsPredictionPopupOpen(false)}>
            <div className="popup-icon-circle"><img src="/img/icons/land.svg" alt="Land" /></div>
            <div className="popup-label">Land price prediction</div>
          </Link>
        </div>
      </div>

      <Link to="/" className={`nav-item ${isActive('/')}`}>
        <img src="/img/icons/home.svg" alt="Home" className="nav-icon" />
        <span className="nav-text">Home</span>
      </Link>

      {/* --- UPDATED: Added onClick interceptor --- */}
      <Link 
        to="/dashboard" 
        className={`nav-item ${isActive('/dashboard')}`}
        onClick={handleProtectedNavigation}
      >
        <img src="/img/icons/dashboard.svg" alt="Dashboard" className="nav-icon" />
        <span className="nav-text">Dashboard</span>
      </Link>

      <Link to="/askreva" state={{ from: location.pathname }} className={`nav-item ${isActive('/askreva')}`}>
        <img src="/img/icons/chat.svg" alt="Chat" className="nav-icon" />
        <span className="nav-text">Ask Rēva</span>
      </Link>
    </nav>
  );
};

export default MobileBottomNav;