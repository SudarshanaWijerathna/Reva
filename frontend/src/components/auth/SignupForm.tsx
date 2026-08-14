import { type FormEvent, useState } from "react";
import { API_BASE_URL } from "../../config/api";
import GoogleButton from "./GoogleButton";

export default function SignupForm({ onSwitch }: { onSwitch: () => void }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState(""); 
  const [isAgreed, setIsAgreed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // --- NEW: State to control the Terms & Conditions popup ---
  const [showTerms, setShowTerms] = useState(false);
  
  const [errors, setErrors] = useState({ fullName: "", email: "", password: "", confirmPassword: "", general: "" });
  const [success, setSuccess] = useState("");

  const handleSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSuccess("");
    
    let newErrors = { fullName: "", email: "", password: "", confirmPassword: "", general: "" };
    let isValid = true;

    if (!fullName.trim()) {
      newErrors.fullName = "Full name is required";
      isValid = false;
    }
    if (!email.trim() || !/^\S+@\S+\.\S+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
      isValid = false;
    }
    if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
      isValid = false;
    }
    if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
      isValid = false;
    }

    setErrors(newErrors);
    if (!isValid) return;

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: email.trim(),
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "Registration failed");
      }

      setSuccess("Account created successfully. Please login.");
      
      localStorage.setItem("reva_backup_name", fullName.trim());

      setFullName("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      
      setTimeout(() => onSwitch(), 700);
    } catch (err) {
      setErrors({ ...newErrors, general: err instanceof Error ? err.message : "Registration failed" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // Added position: relative here so the terms overlay stays locked inside the form
    <div className="auth-form-inner fade-in" style={{ position: 'relative' }}>
      
      {/* --- NEW: The Terms and Privacy Overlay --- */}
      {showTerms && (
        <div 
          className="fade-in"
          style={{
            position: 'absolute',
            top: -10,
            left: -10,
            right: -10,
            bottom: -10,
            backgroundColor: '#ffffff',
            zIndex: 50,
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
          }}
        >
          <h3 style={{ marginTop: 0, marginBottom: '16px', color: '#000020' }}>Terms & Privacy Policy</h3>
          
          <div style={{ flex: 1, overflowY: 'auto', fontSize: '13px', lineHeight: '1.6', color: '#4a4a68', paddingRight: '8px', marginBottom: '16px' }}>
            <p><strong>1. Introduction</strong><br/>
            Welcome to Rēva, your Intelligent Real Estate Virtual Assistant. By creating an account, you agree to these terms.</p>
            
            <p><strong>2. AI Estimations, Not Appraisals</strong><br/>
            Rēva uses machine learning, location intelligence, and historical data to predict housing, rental, and land prices. These predictions are data-driven estimates designed for decision-support and do not constitute official financial, legal, or professional property appraisals.</p>
            
            <p><strong>3. Your Data Stays With You (Privacy)</strong><br/>
            Privacy is at our core. The property information and details you provide are processed securely and used exclusively to generate predictions and insights. We do not sell your personal data to third parties, nor do we employ hidden tracking mechanisms.</p>
            
            <p><strong>4. User Responsibilities</strong><br/>
            You agree to provide accurate information to ensure the highest quality of AI analysis. You agree not to misuse the platform, reverse-engineer the machine learning models, or use the service for any unlawful real estate practices.</p>
            
            <p><strong>5. Limitation of Liability</strong><br/>
            Real estate markets are subject to rapid change. Rēva is not liable for any financial losses or real estate decisions made based on the AI predictions provided by this platform.</p>
          </div>

          <button 
            type="button" 
            className="btn-primary" 
            onClick={() => setShowTerms(false)}
            style={{ width: '100%', padding: '12px', fontSize: '14px' }}
          >
            I Understand & Close
          </button>
        </div>
      )}
      {/* ------------------------------------------- */}

      <div className="form-header">
        <h2>Create Account</h2>
        <p>Join Rēva for intelligent real estate predictions</p>
      </div>

      <div className="google-auth-section">
        <GoogleButton text="Sign up with Google" />
        <div className="divider">
          <span className="desktop-only">or Sign up with Email</span>
          <span className="mobile-only">or Sign up with Google</span>
        </div>
      </div>

      <form onSubmit={handleSignup}>
        <div className="input-group">
          <label>Full Name</label>
          <div className="auth-input-wrapper">
            <i className="fa-regular fa-user auth-field-icon"></i>
            <input
              type="text"
              className={`reva-input ${errors.fullName ? "input-error" : ""}`}
              placeholder="Type your full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          {errors.fullName && <span className="error-text">{errors.fullName}</span>}
        </div>

        <div className="input-group">
          <label>Email</label>
          <div className="auth-input-wrapper">
            <i className="fa-regular fa-envelope auth-field-icon"></i>
            <input
              type="email"
              className={`reva-input ${errors.email ? "input-error" : ""}`}
              placeholder="Type your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          {errors.email && <span className="error-text">{errors.email}</span>}
        </div>

        <div className="input-group">
          <label>Password</label>
          <div className="auth-input-wrapper">
            <i className="fa-solid fa-lock auth-field-icon"></i>
            <input
              type={showPassword ? "text" : "password"}
              className={`reva-input ${errors.password ? "input-error" : ""}`}
              placeholder="Type your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button
              type="button"
              className="auth-pwd-toggle"
              onClick={() => setShowPassword(!showPassword)}
              title={showPassword ? "Hide password" : "Show password"}
            >
              <i className={`fa-regular ${showPassword ? "fa-eye-slash" : "fa-eye"}`}></i>
            </button>
          </div>
          {errors.password && <span className="error-text">{errors.password}</span>}
        </div>

        <div className="input-group">
          <label>Re-enter Password</label>
          <div className="auth-input-wrapper">
            <i className="fa-solid fa-lock auth-field-icon"></i>
            <input
              type={showConfirmPassword ? "text" : "password"}
              className={`reva-input ${errors.confirmPassword ? "input-error" : ""}`}
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
            <button
              type="button"
              className="auth-pwd-toggle"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              title={showConfirmPassword ? "Hide password" : "Show password"}
            >
              <i className={`fa-regular ${showConfirmPassword ? "fa-eye-slash" : "fa-eye"}`}></i>
            </button>
          </div>
          {errors.confirmPassword && <span className="error-text">{errors.confirmPassword}</span>}
        </div>

        <div className="form-actions">
          <label className="check-group" style={{ display: 'flex', alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={isAgreed}
              onChange={(e) => setIsAgreed(e.target.checked)}
              required
            />
            {/* --- UPDATED: Clickable Text --- */}
            <span style={{ marginLeft: '8px' }}>
              I agree to{' '}
              <button 
                type="button" 
                onClick={() => setShowTerms(true)}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  color: '#4445ff', 
                  cursor: 'pointer', 
                  padding: 0, 
                  font: 'inherit', 
                  textDecoration: 'underline',
                  fontWeight: 500
                }}
              >
                Terms & Privacy
              </button>
            </span>
          </label>
        </div>

        {errors.general && <p style={{ color: "#d93025", marginBottom: 12 }}>{errors.general}</p>}
        {success && <p style={{ color: "#188038", marginBottom: 12 }}>{success}</p>}

        <button type="submit" className="btn-login" disabled={isLoading || !isAgreed}>
          {isLoading ? "Creating..." : "Create Account"}
        </button>
      </form>

      <div className="form-footer">
        <span>Already have an account?</span>
        <a onClick={onSwitch} style={{ cursor: 'pointer' }}>Login here</a>
      </div>
    </div>
  );
}