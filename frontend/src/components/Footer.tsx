import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="reva-footer">
      <div className="reva-footer-container">
        <div className="footer-section">
          <h3>Rēva</h3>
          <p>Rēva (Real Estate Virtual Assistant) is an academic project developed to explore the application of machine learning and location intelligence in real estate price analysis.</p>
        </div>
        <div className="footer-section">
          <h4>Academic Context</h4>
          <p>Developed as part of a university coursework and research initiative in data science and artificial intelligence.</p>
          <p className="footer-muted">This system is intended for educational and research purposes only.</p>
        </div>
        <div className="footer-section footer-logo">
          {/* Images in public/ are accessed from root / */}
          <img src="/img/university-logo.png" alt="University Logo" />
          <span>University of Moratuwa</span>
        </div>
      </div>
      <div className="footer-bottom">
        <p>© 2026 Rēva Project · All rights reserved · Educational Use Only</p>
      </div>
    </footer>
  );
};

export default Footer;