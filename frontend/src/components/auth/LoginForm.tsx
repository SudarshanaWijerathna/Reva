import GoogleButton from "./GoogleButton";

export default function LoginForm({ onSwitch }: { onSwitch: () => void }) {
  return (
    <div className="fade-in">
      <div className="form-header">
        <h2>Login to your Account</h2>
        <p>See what is going on with your property portfolio</p>
      </div>

      <GoogleButton text="Continue with Google" />

      <div className="divider">or Sign in with Email</div>

      <form>
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
            <input type="checkbox" /> Remember Me
          </label>
          <a href="#" className="forgot-link">Forgot Password?</a>
        </div>

        <button type="submit" className="btn-login">Login</button>
      </form>

      <div className="form-footer">
        Not Registered Yet? <a onClick={onSwitch}>Create an account</a>
      </div>
    </div>
  );
}
