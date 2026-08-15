import { useLocation, useNavigate } from "react-router-dom";
import LoginForm from "./LoginForm";
import SignupForm from "./SignupForm";

export default function LoginFormWrapper() {
  const location = useLocation();
  const navigate = useNavigate();

  // Support both explicit auth routes and route state-driven toggling.
  const isSignup = location.pathname === '/signup' || location.state?.mode === 'signup';

  const switchMode = (mode: 'login' | 'signup') => {
    navigate(mode === 'signup' ? '/signup' : '/login', {
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
