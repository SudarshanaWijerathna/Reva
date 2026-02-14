import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const [isSticky, setIsSticky] = useState<boolean>(false);
  const location = useLocation();

  useEffect(() => {
    let scrollTimeout: ReturnType<typeof setTimeout> | null = null;

    const handleScroll = () => {
      if (scrollTimeout) return;

      scrollTimeout = setTimeout(() => {
        setIsSticky(window.scrollY > 300);
        scrollTimeout = null;
      }, 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isActive = (path: string): string =>
    location.pathname === path ? 'selected' : '';

  const isPrediction = location.pathname.includes('price');

  return (
    <nav className={`navbar ${isSticky ? 'sticky' : ''}`} id="mainNavbar">
      <div className="nav-container">
        <div className="nav-brand">
          <svg width="32" height="32" viewBox="0 0 276 272">
            <path className="cls-1" d="M78.36,86.36v99.27c0,4.43-3.59,8.02-8.02,8.02h-17.54c-29.15,0-52.8-23.62-52.8-52.79v-44.61c0-9.9,8.02-17.92,17.92-17.92h52.41c4.43,0,8.02,3.59,8.02,8.02Z"/>
            <path className="cls-1" d="M193.71,193.66v16.05c0,34.39-27.88,62.28-62.28,62.28H43.28c-15.97,0-23.96-19.31-12.67-30.6l45.39-45.38c1.5-1.5,3.55-2.35,5.67-2.35h112.04Z"/>
            <path className="cls-1" d="M223.2,208.19h-11.64c-2.13,0-4.17-.85-5.67-2.35l-45.63-45.62c-7.24-7.24-2.11-19.62,8.13-19.62h99.58c4.43,0,8.02,3.59,8.02,8.02v6.76c0,29.14-23.65,52.79-52.8,52.79l.02.02Z"/>
            <path className="cls-1" d="M193.71,140.62l56.93-56.91c21.56-21.56,18.09-57.91-7.71-74.16-9.6-6.05-20.97-9.54-33.16-9.54H43.28c-15.97,0-23.96,19.31-12.67,30.6l45.4,45.39c1.5,1.5,3.55,2.35,5.67,2.35h104c4.43,0,8.02,3.59,8.02,8.02v54.25Z"/>
          </svg>
          <span className="nav-title">rēva</span>
        </div>

        <ul className="nav-links">
          <li className={isActive('/')}><Link to="/">Home</Link></li>
          <li className={isActive('/dashboard')}><Link to="/dashboard">Dashboard</Link></li>
          <li className={isPrediction ? 'selected' : ''}><Link to="/land-price">Predictions</Link></li>
          <li className={isActive('/contact')}><Link to="/contact">Contact</Link></li>
        </ul>

        <div className="nav-actions">
          <Link to="/login" className="btn-outline">Sign Up</Link>
          <Link to="/login" className="btn-primary">Login</Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
