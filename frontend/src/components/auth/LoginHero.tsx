import { useAuth } from '../../context/AuthContext';

export default function LoginHero() {
  const { authMode, closeAuthModal } = useAuth();
  const isSignup = authMode === 'signup';

  return (
    <div className="login-hero">
      
      {/* Added flex positioning so Logo is left, Close is right */}
      <div className="hero-top-bar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
        <div className="mobile-hero-logo mobile-only">
          <img className="hero-reva-image" src="/img/logo.png" alt="Rēva" style={{ width: '100px', marginLeft: '-10px' }} />
        </div>

        <button 
          onClick={closeAuthModal} 
          className="hero-back-btn" 
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '15px', fontWeight: 600, color: '#4a4a68' }}
        >
          <i className="fa-solid fa-xmark"></i> Close
        </button>
      </div>

      <i className="fa-solid fa-robot hero-shape shape-1"></i>
      <i className="fa-solid fa-chart-simple hero-shape shape-2"></i>
      <i className="fa-solid fa-building hero-shape shape-3"></i>

      <div className="hero-content" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div className="main-logo-large desktop-only">
          <img src="/img/banner-hero-image.gif" alt="reva-gif-image" />
        </div>

        <div className="desktop-only">
          <h1>Your real estate virtual assistant</h1>
          <p>Start for free and get intelligent AI-driven insights for smarter property decisions.</p>
        </div>

        {/* Pushed to the bottom of the hero section using margin-top: auto */}
        <div className="mobile-only hero-mobile-titles" style={{ marginTop: 'auto', marginBottom: '20px' }}>
          <h1 style={{ fontSize: '28px', color: '#000020', marginBottom: '8px' }}>
            {isSignup ? "Create Account" : "Login to your Account"}
          </h1>
          <p style={{ color: '#4a4a68', fontSize: '14px', lineHeight: '1.5' }}>
            {isSignup ? "Join Rēva for intelligent real estate predictions" : "See what is going on with your property portfolio"}
          </p>
        </div>
      </div>
      
    </div>
  );
}