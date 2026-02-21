// src/pages/LoginPage.tsx
import LoginHero from "../components/auth/LoginHero";
import LoginFormWrapper from "../components/auth/LoginFormWrapper";

// 👇 ADD THIS LINE to load the styles
import "../assets/css/auth.css"; 

export default function LoginPage() {
  return (
    <div className="login-container">
      <LoginHero />
      <LoginFormWrapper />
    </div>
  );
}