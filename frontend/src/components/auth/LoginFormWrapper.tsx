import { useState } from "react";
import LoginForm from "./LoginForm";
import SignupForm from "./SignupForm";

export default function LoginFormWrapper() {
  const [isSignup, setIsSignup] = useState(false);

  return (
    <div className="login-form-wrapper">
      <div className="nav-brand-small">
        <svg viewBox="0 0 276 272">
          <path d="M78.3591 78.3405V193.66H52.7974C23.6458 193.66 0 170.037 0 140.875V78.3405H78.3591Z" />
          <path d="M193.706 193.66V209.707C193.706 244.098 165.814 271.983 131.415 271.983H0L78.3418 193.66H193.706Z" />
          <path d="M223.203 208.189H208.238L140.632 140.599H275.983V155.387C275.983 184.531 252.337 208.172 223.185 208.172Z" />
          <path d="M193.706 140.616L272.048 62.2927C272.065 27.885 244.173 0 209.757 0H0L78.3591 78.3404H193.706V140.616Z" />
        </svg>
        <span className="nav-title">rēva</span>
      </div>

      {isSignup ? (
        <SignupForm onSwitch={() => setIsSignup(false)} />
      ) : (
        <LoginForm onSwitch={() => setIsSignup(true)} />
      )}
    </div>
  );
}
