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
  );
}