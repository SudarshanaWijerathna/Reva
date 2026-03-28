import { useLocation, useNavigate } from "react-router-dom";
import LoginForm from "./LoginForm";
import SignupForm from "./SignupForm";

export default function LoginFormWrapper() {
  const location = useLocation();
  const navigate = useNavigate();

  // Derive state directly from the router so LoginHero always matches
  const isSignup = location.state?.mode === 'signup';

  // Instead of internal state, update the URL state so LoginHero sees it too!
  const switchMode = (mode: 'login' | 'signup') => {
    navigate(location.pathname, {
      replace: true,
      state: { ...location.state, mode }
    });
  };

  return (
    <>
      {/* --- THE MOBILE FIX: CSS Grid Injection --- */}
      <style>{`
        @media (max-width: 768px) {
          /* 1. Force the parent Modal Container to be a Full-Screen Grid */
          div:has(> .login-form-wrapper) {
            display: grid !important;
            grid-template-rows: 1fr 2.5fr !important; /* Divides into 2 vertical sections using fr units */
            width: 100vw !important;
            height: 100dvh !important; /* dvh adapts perfectly to mobile browser bars */
            max-width: 100vw !important;
            max-height: 100dvh !important;
            border-radius: 0 !important;
            overflow: hidden !important;
            background-color: #f4f7f9 !important; /* Solid background to replace the blur */
            padding: 0 !important;
            margin: 0 !important;
            top: 0 !important;
            left: 0 !important;
            transform: none !important;
          }

          /* 2. Remove the blur from the dark overlay behind the modal */
          div:has(> div > .login-form-wrapper) {
             backdrop-filter: none !important;
          }

          /* 3. The Hero Section (Top 1fr) */
          .login-hero {
            position: relative !important;
            width: 100% !important;
            height: 100% !important;
            min-height: 0 !important; /* Critical to prevent grid blowout */
            border-radius: 0 !important;
            padding: 24px 24px 0px 24px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
          }

          /* 4. The Form Section (Bottom 2.5fr) - Make it scrollable! */
          .login-form-wrapper {
            width: 100% !important;
            height: 100% !important;
            min-height: 0 !important; /* Critical to prevent grid blowout */
            overflow-y: auto !important; /* The magic scroll property */
            padding: 24px 24px 100px 24px !important; /* Extra bottom padding for thumb reachability */
            background-color: #ffffff !important;
            border-top-left-radius: 28px !important; /* Creates a modern overlapping card effect */
            border-top-right-radius: 28px !important;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.05) !important;
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