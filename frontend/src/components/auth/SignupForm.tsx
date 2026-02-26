import { type FormEvent, useState } from "react";
import { API_BASE_URL } from "../../config/api";
import GoogleButton from "./GoogleButton";

export default function SignupForm({ onSwitch }: { onSwitch: () => void }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isAgreed, setIsAgreed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSignup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName.trim(), // optional extra from frontend field
          email: email.trim(),
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "Registration failed");
      }

      setSuccess("Account created successfully. Please login.");
      setFullName("");
      setEmail("");
      setPassword("");
      setTimeout(() => onSwitch(), 700);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fade-in">
      <div className="form-header">
        <h2>Create Account</h2>
        <p>Join Reva for intelligent real estate predictions</p>
      </div>

      <GoogleButton text="Sign up with Google" />
      <div className="divider">or Sign up with Email</div>

      <form onSubmit={handleSignup}>
        <div className="input-group">
          <label>Full Name</label>
          <input
            type="text"
            className="reva-input"
            placeholder="John Doe"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
        </div>

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
              checked={isAgreed}
              onChange={(e) => setIsAgreed(e.target.checked)}
              required
            />
            I agree to Terms & Privacy
          </label>
        </div>

        {error && <p style={{ color: "#d93025", marginBottom: 12 }}>{error}</p>}
        {success && <p style={{ color: "#188038", marginBottom: 12 }}>{success}</p>}

        <button type="submit" className="btn-login" disabled={isLoading || !isAgreed}>
          {isLoading ? "Creating..." : "Create Account"}
        </button>
      </form>

      <div className="form-footer">
        Already have an account? <a onClick={onSwitch}>Login here</a>
      </div>
    </div>
  );
}