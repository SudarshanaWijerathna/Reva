import { type FormEvent, useState } from "react";
import { useLocation } from "react-router-dom";
import { API_BASE_URL } from "../../config/api";
import { checkAdminAccess, persistAuthSession } from "../../services/authService";
import GoogleButton from "./GoogleButton";
import { useAuth } from "../../context/AuthContext";

export default function LoginForm({ onSwitch }: { onSwitch: () => void }) {
  const { closeAuthModal, redirectPath } = useAuth();
  const location = useLocation();

  const requestedFrom = typeof location.state?.from === 'string' ? location.state.from : null;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // --- NEW: State to track password visibility ---
  const [showPassword, setShowPassword] = useState(false);
  
  const [errors, setErrors] = useState({ email: "", password: "", general: "" });

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    let newErrors = { email: "", password: "", general: "" };
    let isValid = true;

    if (!email.trim() || !/^\S+@\S+\.\S+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
      isValid = false;
    }
    if (!password.trim()) {
      newErrors.password = "Password is required";
      isValid = false;
    }

    setErrors(newErrors);
    if (!isValid) return;

    setIsLoading(true);

    try {
      const body = new URLSearchParams();
      body.append("username", email.trim()); 
      body.append("password", password);

      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "Login failed");
      }

      const storage = rememberMe ? localStorage : sessionStorage;

      // --- 1. MERGED: Check Admin Access (From Incoming Branch) ---
      let isAdmin = false;
      try {
        isAdmin = await checkAdminAccess(data.access_token);
      } catch (adminErr) {
        console.error("Failed to check admin status:", adminErr);
      }

      // --- 2. MERGED: Fetch Profile with 404 Fallback (From HEAD) ---
      let fullName: string | null = null;
      try {
        const profileRes = await fetch(`${API_BASE_URL}/users/me`, {
          method: 'GET',
          headers: { 
            'Authorization': `Bearer ${data.access_token}`,
            'Accept': 'application/json'
          }
        });

        if (profileRes.ok) {
          const profileData = await profileRes.json();
          const userName = profileData.full_name; 
          
          if (userName) {
            fullName = userName;
          }
        } else {
          const backupName = localStorage.getItem("reva_backup_name");
          if (backupName) {
            fullName = backupName;
          }
        }
      } catch (profileErr) {
        console.error("Failed to fetch profile info:", profileErr);
      }

      persistAuthSession(storage, {
        accessToken: data.access_token,
        tokenType: data.token_type,
        email: email.trim(),
        fullName,
        isAdmin,
      });

      closeAuthModal();

      // --- 3. MERGED: Routing Logic ---
      // Prioritize Admin routing, then explicit redirects, then fallback to dashboard
      const fallbackDestination = isAdmin ? '/admin' : (redirectPath || '/dashboard');
      const pathToGo = requestedFrom && requestedFrom !== '/login' ? requestedFrom : fallbackDestination;
      
      if (pathToGo) {
        window.location.href = pathToGo; // Hard redirect to force navbar updates
      } else {
        window.location.reload(); 
      }
      
    } catch (err) {
      setErrors({ ...newErrors, general: err instanceof Error ? err.message : "Login failed" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form-inner fade-in">

       <div className="form-header">
        <h2>Login to your Account</h2>
        <p>See what is going on with your property portfolio</p>
      </div>

      <div className="google-auth-section">
        <GoogleButton text="Continue with Google" />
        <div className="divider">
          <span className="desktop-only">or Sign in with Email</span>
          <span className="mobile-only">or Sign in with Google</span>
        </div>
      </div>

      <form onSubmit={handleLogin}>
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

        {/* --- Password field with visibility toggle --- */}
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

        <div className="form-actions">
          <label className="check-group">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            Remember Me
          </label>
          <a href="#" className="forgot-link">Forgot Password?</a>
        </div>

        {errors.general && <p style={{ color: "#d93025", marginBottom: 12 }}>{errors.general}</p>}

        <button type="submit" className="btn-login" disabled={isLoading}>
          {isLoading ? "Logging in..." : "Login"}
        </button>
      </form>

      <div className="form-footer">
        <span>Not Registered Yet?</span>
        <a onClick={onSwitch} style={{ cursor: 'pointer' }}>Create an account</a>
      </div>
    </div>
  );
}
