import GoogleButton from "./GoogleButton";

export default function SignupForm({ onSwitch }: { onSwitch: () => void }) {
  return (
    <div className="fade-in">
      <div className="form-header">
        <h2>Create Account</h2>
        <p>Join Reva for intelligent real estate predictions</p>
      </div>

      <GoogleButton text="Sign up with Google" />

      <div className="divider">or Sign up with Email</div>

      <form>
        <div className="input-group">
          <label>Full Name</label>
          <input type="text" className="reva-input" placeholder="John Doe" />
        </div>

        <div className="input-group">
          <label>Email</label>
          <input type="email" className="reva-input" placeholder="mail@example.com" />
        </div>

        <div className="input-group">
          <label>Password</label>
          <input type="password" className="reva-input" placeholder="••••••••••••" />
        </div>

        <div className="form-actions">
          <label className="check-group">
            <input type="checkbox" required /> I agree to Terms & Privacy
          </label>
        </div>

        <button type="submit" className="btn-login">Create Account</button>
      </form>

      <div className="form-footer">
        Already have an account? <a onClick={onSwitch}>Login here</a>
      </div>
    </div>
  );
}
