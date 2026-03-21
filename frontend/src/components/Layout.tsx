import React, { useState, useEffect } from "react";
import DesktopNavbar from './navigation/DesktopNavbar';
import MobileBottomNav from './navigation/MobileBottomNav';
import Footer from './Footer';
import { Link } from "react-router-dom";

// FIX: Used React.ReactNode directly to avoid the verbatimModuleSyntax import error
interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);
  const [isFixedHeaderVisible, setIsFixedHeaderVisible] = useState(false);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (!isMobile) return;

    // FIX: Added 'as HTMLElement' to satisfy TypeScript's offsetHeight requirement
    const mainWrapper = document.getElementById('mainWrapper') as HTMLElement | null;
    const mainHeader = document.getElementById('mainHeader') as HTMLElement | null;
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

    const handleScroll = () => {
      if (mainHeader && window.scrollY > (mainHeader.offsetHeight + 10)) {
        setIsFixedHeaderVisible(true);
      } else {
        setIsFixedHeaderVisible(false);
      }

      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        snapBackFooter();
      }, 1000);
    };

    window.addEventListener('touchend', snapBackFooter);
    window.addEventListener('mouseup', snapBackFooter);
    window.addEventListener('scroll', handleScroll);

    return () => {
      window.removeEventListener('touchend', snapBackFooter);
      window.removeEventListener('mouseup', snapBackFooter);
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(scrollTimeout);
    };
  }, [isMobile]);

  return (
    <>
      <div className="global-background-overlay">
        <i className="fa-solid fa-house bg-float-icon shape-1"></i>
        <i className="fa-solid fa-chart-line bg-float-icon shape-2"></i>
        <i className="fa-solid fa-city bg-float-icon shape-3"></i>
      </div>

      {!isMobile ? (
        <DesktopNavbar />
      ) : (
        <header className={`top-header fixed-header ${isFixedHeaderVisible ? 'visible' : ''}`} id="fixedHeader">
          <Link to="/">
            <img src="/img/logo.png" alt="Reva Logo" className="header-logo" />
          </Link>
          <div className="header-profile">
            <span className="user-name">Isuru Sudarshana</span>
            <img src="https://i.pravatar.cc/150?img=11" alt="Isuru Sudarshana" className="user-avatar" />
          </div>
        </header>
      )}

      <div className="main-wrapper" id="mainWrapper">
        {isMobile && (
          <header className="top-header" id="mainHeader">
            <Link to="/">
              <img src="/img/logo.png" alt="Reva Logo" className="header-logo" />
            </Link>
            <div className="header-profile">
              <span className="user-name">Isuru Sudarshana</span>
              <img src="https://i.pravatar.cc/150?img=11" alt="Isuru Sudarshana" className="user-avatar" />
            </div>
          </header>
        )}

        <main>
            {children}
        </main>
        
        {isMobile && <MobileBottomNav />}
      </div>
      
      <Footer />
    </>
  );
};

export default Layout;