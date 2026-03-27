import { useAuth } from '../../context/AuthContext';

export default function LoginHero() {
  // Use the global context instead of the React Router location state
  const { authMode, closeAuthModal } = useAuth();
  const isSignup = authMode === 'signup';

  return (
    <div className="login-hero">
      
      <div className="hero-top-bar">

        <div className="mobile-hero-logo mobile-only">
          <img className="hero-reva-image" src="/img/logo.png" alt="Rēva" style={{ width: '100px', marginLeft: '-10px' }} />
        </div>

        <button 
          onClick={closeAuthModal} 
          className="hero-back-btn" 
        >
          <i className="fa-solid fa-xmark"></i> Close
        </button>

        
      </div>

      <i className="fa-solid fa-robot hero-shape shape-1"></i>
      <i className="fa-solid fa-chart-simple hero-shape shape-2"></i>
      <i className="fa-solid fa-building hero-shape shape-3"></i>

      <div className="hero-content">
        <div className="main-logo-large desktop-only">
          <img src="/img/banner-hero-image.gif" alt="reva-gif-image" />
        </div>

        <div className="desktop-only">
          <h1>Your real estate virtual assistant</h1>
          <p>Start for free and get intelligent AI-driven insights for smarter property decisions.</p>
        </div>

        <div className="mobile-only hero-mobile-titles">
          <h1>{isSignup ? "Create Account" : "Login to your Account"}</h1>
          <p>{isSignup ? "Join Reva for intelligent real estate predictions" : "See what is going on with your property portfolio"}</p>
        </div>
      </div>
    </div>
  );
}