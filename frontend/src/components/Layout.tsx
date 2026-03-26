import React, { useState, useEffect } from "react";
import DesktopNavbar from './navigation/DesktopNavbar';
import MobileHeader from './navigation/MobileHeader'; // <-- Import the component we built!
import MobileBottomNav from './navigation/MobileBottomNav';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (!isMobile) return;

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
      // Removed the sticky header state logic from here because MobileHeader.tsx handles it now!
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

      {!isMobile && <DesktopNavbar />}

      <div className="main-wrapper" id="mainWrapper">
        
        {/* Our MobileHeader component now handles both the static and fixed headers! */}
        {isMobile && <MobileHeader />}

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