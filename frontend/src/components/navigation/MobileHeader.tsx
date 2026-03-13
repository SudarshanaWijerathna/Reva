import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const MobileHeader: React.FC = () => {
  const [isHeaderSticky, setIsHeaderSticky] = useState<boolean>(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsHeaderSticky(window.scrollY > 90);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      {/* SCROLLING FIXED HEADER */}
      <header className={`top-header fixed-header ${isHeaderSticky ? 'visible' : ''}`} id="fixedHeader">
        <Link to="/">
          <img src="/src/assets/logo.png" alt="Reva Logo" className="header-logo" />
        </Link>
        <div className="header-profile">
          <span className="user-name">Isuru Sudarshana</span>
          <img src="https://i.pravatar.cc/150?img=11" alt="Profile" className="user-avatar" />
        </div>
      </header>

      {/* MAIN STATIC HEADER */}
      <header className="top-header" id="mainHeader">
        <Link to="/">
          <img src="/src/assets/logo.png" alt="Reva Logo" className="header-logo" />
        </Link>
        <div className="header-profile">
          <span className="user-name">Isuru Sudarshana</span>
          <img src="https://i.pravatar.cc/150?img=11" alt="Profile" className="user-avatar" />
        </div>
      </header>
    </>
  );
};

export default MobileHeader;