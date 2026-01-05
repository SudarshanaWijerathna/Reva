import React, { ReactNode } from 'react';
import Navbar from './Navbar';
import Footer from './Footer';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <>
      <div className="global-background-overlay">
        <i className="fa-solid fa-house bg-float-icon shape-1"></i>
        <i className="fa-solid fa-chart-line bg-float-icon shape-2"></i>
        <i className="fa-solid fa-city bg-float-icon shape-3"></i>
      </div>

      <a href="chatbot.html" className="chatbot-toggler">
        <i className="fa-solid fa-robot"></i>
      </a>

      <Navbar />

      {/* Page Content injected here */}
      {children}
      
      {/* We don't put Footer here automatically because your 
          index.html had it inside 'container', but usually 
          it's cleaner to put it here. Let's keep it flexible.
          For now, we will add Footer manually in pages to match your structure exactly.
      */}
    </>
  );
};

export default Layout;