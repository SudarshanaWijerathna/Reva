// src/pages/LoginPage.tsx
import { useNavigate } from "react-router-dom";
import LoginHero from "../components/auth/LoginHero";
import LoginFormWrapper from "../components/auth/LoginFormWrapper";
import "../assets/css/auth.css"; 

export default function LoginPage() {
  const navigate = useNavigate();

  return (
    <div className="login-container">
      <button 
        type="button"
        onClick={() => navigate('/')} 
        className="auth-close-btn"
        aria-label="Back to home"
        title="Back to home"
      >
        <i className="fa-solid fa-xmark"></i>
      </button>
      <LoginHero />
      <LoginFormWrapper />
    </div>
  );
}