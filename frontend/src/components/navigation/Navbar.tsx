import React, { useState, useEffect } from 'react';
import DesktopNavbar from './DesktopNavbar';
import MobileHeader from './MobileHeader';
import MobileBottomNav from './MobileBottomNav';

const Navbar: React.FC = () => {
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (isMobile) {
    return (
      <>
        <MobileHeader />
        <MobileBottomNav />
      </>
    );
  }

  return <DesktopNavbar />;
};

export default Navbar;