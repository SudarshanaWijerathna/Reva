import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../../config/api";
import GoogleButton from "./GoogleButton";

export default function LoginForm({ onSwitch }: { onSwitch: () => void }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const body = new URLSearchParams();
      body.append("username", email.trim()); // backend expects username field for OAuth2 form
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
      storage.setItem("access_token", data.access_token);
      storage.setItem("token_type", data.token_type);
      storage.setItem("user_email", email.trim());

      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fade-in">
      <div className="form-header">
        <h2>Login to your Account</h2>
        <p>See what is going on with your property portfolio</p>
      </div>

      <GoogleButton text="Continue with Google" />
      <div className="divider">or Sign in with Email</div>

      <form onSubmit={handleLogin}>
        <div className="input-group">
          <label>Email</label>
          <input
            type="email"
            className="reva-input"
            placeholder="mail@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="input-group">
          <label>Password</label>
          <input
            type="password"
            className="reva-input"
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
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

        {error && <p style={{ color: "#d93025", marginBottom: 12 }}>{error}</p>}

        <button type="submit" className="btn-login" disabled={isLoading}>
          {isLoading ? "Logging in..." : "Login"}
        </button>
      </form>

      <div className="form-footer">
        Not Registered Yet? <a onClick={onSwitch}>Create an account</a>
      </div>
    </div>
  );
}