import { useAuth } from '../../context/AuthContext';
import LoginHero from './LoginHero';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';
import '../../assets/css/auth.css'; // Ensure this points to your polished CSS

export default function AuthModal() {
  const { isModalOpen, authMode, closeAuthModal, switchAuthMode } = useAuth();

  // If the master switch is off, render absolutely nothing
  if (!isModalOpen) return null;

  return (
    // The fixed, blurred overlay
    <div className="auth-modal-overlay" onClick={closeAuthModal}>
      
      {/* We use e.stopPropagation() here so that clicking INSIDE the white box 
        doesn't accidentally close the modal. Only clicking the blurred background closes it.
      */}
      <div 
        className="auth-modal-content" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="login-container modal-version">
          
          <LoginHero />

          <div className="login-form-wrapper">
            <div className="nav-brand-small desktop-only">
              <img className="hero-reva-image" src="/img/logo.png" alt="Rēva" style={{ width: '120px', marginLeft: '-10px' }} />
            </div>

            {/* Render the correct form based on the Global Context, passing the switcher function */}
            {authMode === 'signup' ? (
              <SignupForm onSwitch={() => switchAuthMode('login')} />
            ) : (
              <LoginForm onSwitch={() => switchAuthMode('signup')} />
            )}
          </div>

        </div>
      </div>
    </div>
  );
}