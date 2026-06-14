import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import '../assets/css/support.css'

const Support: React.FC = () => {
  const [userName, setUserName] = useState<string | null>(null);

  // Dynamically check if a user is logged in to show their name on the support ticket
  useEffect(() => {
    const storedName = localStorage.getItem('user_name') || sessionStorage.getItem('user_name');
    if (storedName) {
      setUserName(storedName);
    }
  }, []);

  return (
    <Layout>
      <div className="contact-wrapper">
        
        <div className="contact-header">
            <h1>Rēva Support</h1>
            <p>Need help with your predictions or account? Our support team is here to help.</p>
        </div>

        <div className="contact-grid">
            
            {/* Information Card (Stacks on TOP in mobile) */}
            <div className="contact-info-card">
                <div className="circle-deco cd-1"></div>
                <div className="circle-deco cd-2"></div>
                <h3>Support Information</h3>
                <p>Fill out the form and our technical team will get back to you within 24 hours.</p>

                <ul className="info-list">
                    <li className="info-item">
                        <i className="fa-solid fa-phone"></i>
                        <div>
                            <span>Support Hotline</span>
                            <strong>+94 11 265 0301</strong>
                        </div>
                    </li>
                    <li className="info-item">
                        <i className="fa-solid fa-envelope"></i>
                        <div>
                            <span>Email Support</span>
                            <strong>support@reva.lk</strong>
                        </div>
                    </li>
                    <li className="info-item">
                        <i className="fa-solid fa-location-dot"></i>
                        <div>
                            <span>Headquarters</span>
                            <strong>University of Moratuwa,<br/>Katubedda, Sri Lanka</strong>
                        </div>
                    </li>
                </ul>

                <div className="social-links">
                    <a href="#"><i className="fa-brands fa-twitter"></i></a>
                    <a href="#"><i className="fa-brands fa-instagram"></i></a>
                    <a href="#"><i className="fa-brands fa-linkedin-in"></i></a>
                    <a href="#"><i className="fa-brands fa-facebook-f"></i></a>
                </div>
            </div>

            {/* Form Card (Stacks on BOTTOM in mobile) */}
            <div className="contact-form-card">
                {/* Only show the badge if the user is actually logged in */}
                {userName && (
                    <div className="user-badge">
                        <i className="fa-solid fa-user-check"></i> Sending as: {userName}
                    </div>
                )}

                <form onSubmit={(e) => e.preventDefault()}>
                    <div className="form-group">
                        <label>What do you need help with?</label>
                        <select className="contact-input">
                            <option>General Support Inquiry</option>
                            <option>Report a Technical Issue</option>
                            <option>Prediction Accuracy Inquiry</option>
                            <option>Account Management</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Message</label>
                        <textarea className="contact-input" placeholder="Please describe your issue in detail..."></textarea>
                    </div>

                    <button type="submit" className="btn-primary" style={{width: '100%'}}>Send Support Request</button>
                </form>
            </div>
        </div>
      </div>
    </Layout>
  );
};

export default Support;