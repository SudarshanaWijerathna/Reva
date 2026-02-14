export default function LoginHero() {
  return (
    <div className="login-hero">
      <a href="/" className="hero-back-btn">
        <i className="fa-solid fa-arrow-left"></i> Back
      </a>

      <i className="fa-solid fa-robot hero-shape shape-1"></i>
      <i className="fa-solid fa-chart-simple hero-shape shape-2"></i>
      <i className="fa-solid fa-building hero-shape shape-3"></i>

      <div className="hero-content">
        <div className="main-logo-large">
          <img src="/img/banner-hero-image.gif" alt="reva-gif-image" />
        </div>

        <h1>Your real estate virtual assistant</h1>
        <p>
          Start for free and get intelligent AI-driven insights for smarter
          property decisions.
        </p>
      </div>
    </div>
  );
}
