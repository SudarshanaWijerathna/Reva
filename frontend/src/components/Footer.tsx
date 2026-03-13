import React, { useState, useEffect } from 'react';

const Footer: React.FC = () => {
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);

  // Update state on window resize
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Rubber Band Effect Logic for Mobile
  useEffect(() => {
    if (!isMobile) return;

    // We target the main wrapper or fallback to root
    const mainWrapper = document.querySelector('.main-wrapper') || document.getElementById('root')?.firstElementChild as HTMLElement;
    let scrollTimeout: ReturnType<typeof setTimeout>;

    const snapBackFooter = () => {
      if (!mainWrapper) return;
      const wrapperBottom = mainWrapper.getBoundingClientRect().bottom;
      
      if (wrapperBottom < window.innerHeight) {
        const targetScroll = Math.max(0, mainWrapper.offsetHeight - window.innerHeight);
        window.scrollTo({
          top: targetScroll,
          behavior: 'smooth'
        });
      }
    };

    window.addEventListener('touchend', snapBackFooter);
    window.addEventListener('mouseup', snapBackFooter);

    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        snapBackFooter();
      }, 1000);
    };

    window.addEventListener('scroll', handleScroll);

    return () => {
      window.removeEventListener('touchend', snapBackFooter);
      window.removeEventListener('mouseup', snapBackFooter);
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(scrollTimeout);
    };
  }, [isMobile]);

  /* --- MOBILE FOOTER --- */
  if (isMobile) {
    return (
      <footer className="reva-footer m-footer">
        <div className="m-footer-grid">
          <div className="m-footer-logo-side">
            {/* Removed the inline style so CSS controls the size */}
            <img src="/img/university-logo.png" alt="University Logo" />
          </div>
          <div className="m-footer-content-side">
            <h4>Academic Context</h4>
            <p>Developed as part of a university coursework and research initiative in data science and artificial intelligence.</p>
          </div>
        </div>
        <div className="m-footer-bottom">
          <p>© 2026 Rēva Project · All rights reserved · Educational Use Only</p>
        </div>
      </footer>
    );
  }

  /* --- DESKTOP FOOTER (Original) --- */
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