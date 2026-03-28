import { useLocation, useNavigate } from "react-router-dom";
import LoginForm from "./LoginForm";
import SignupForm from "./SignupForm";

export default function LoginFormWrapper() {
  const location = useLocation();
  const navigate = useNavigate();

  // Derive state directly from the router so LoginHero always matches
  const isSignup = location.state?.mode === 'signup';

  const switchMode = (mode: 'login' | 'signup') => {
    navigate(location.pathname, {
      replace: true,
      state: { ...location.state, mode }
    });
  };

  return (
    <>
      {/* --- THE MOBILE FIX: Bulletproof Full-Screen Takeover --- */}
      <style>{`
        @media (max-width: 768px) {
          /* 1. Target the Modal Container and force it to take over the screen */
          div:has(> .login-form-wrapper) {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100dvh !important; /* dvh perfectly handles mobile Safari/Chrome address bars */
            max-width: 100vw !important;
            max-height: 100dvh !important;
            z-index: 999999 !important; /* Ensure it floats above the blurred overlay */
            
            display: flex !important;
            flex-direction: column !important;
            
            background-color: #f4f7f9 !important; /* Solid background obscures the blur */
            border-radius: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
          }

          /* 2. Hide the blur effect entirely to save mobile battery/performance */
          div:has(> div > .login-form-wrapper) {
             backdrop-filter: none !important;
             background: transparent !important;
          }

          /* 3. The Hero Section (Top Area) */
          .login-hero {
            position: relative !important;
            width: 100% !important;
            flex: 0 0 auto !important; /* Don't stretch or shrink */
            min-height: 25vh !important;
            border-radius: 0 !important;
            padding: 24px 24px 32px 24px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            margin: 0 !important;
            background-color: transparent !important;
          }

          /* 4. The Form Wrapper (Bottom Area) */
          .login-form-wrapper {
            position: relative !important;
            width: 100% !important;
            flex: 1 1 auto !important; /* Take up all remaining space */
            display: flex !important;
            flex-direction: column !important;
            margin: 0 !important;
            padding: 0 !important;
            min-height: 0 !important; /* CRITICAL: Allows the inner form to scroll without breaking the flexbox */
          }

          /* 5. The Scrollable Form Container */
          .login-form-wrapper > .fade-in {
            width: 100% !important;
            height: 100% !important;
            overflow-y: auto !important; /* The magic scroll property! */
            padding: 32px 24px 100px 24px !important; /* Extra padding at bottom for thumb comfort */
            background-color: #ffffff !important;
            border-top-left-radius: 32px !important; /* Creates the overlapping card effect */
            border-top-right-radius: 32px !important;
            box-shadow: 0 -8px 30px rgba(0,0,0,0.08) !important;
            margin: 0 !important;
          }
          
          .nav-brand-small {
            display: none !important;
          }
        }
      `}</style>

      <div className="login-form-wrapper">
        <div className="nav-brand-small desktop-only">
          <img className="hero-reva-image" src="/img/logo.png" alt="Rēva" style={{ width: '100px', marginLeft: '-10px' }} />
        </div>

        {isSignup ? (
          <SignupForm onSwitch={() => switchMode('login')} />
        ) : (
          <LoginForm onSwitch={() => switchMode('signup')} />
        )}
      </div>
    </>
  );
}