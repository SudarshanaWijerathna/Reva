import React from 'react';
import Layout from '../components/Layout';
import Footer from '../components/Footer';

const Contact: React.FC = () => {
  return (
    <Layout>
      <div className="contact-wrapper">
        
        <div className="contact-header">
            <h1>Get in Touch</h1>
            <p>Have questions about our predictions or want to collaborate? We'd love to hear from you.</p>
        </div>

        <div className="contact-grid">
            
            <div className="contact-info-card">
                <div className="circle-deco cd-1"></div>
                <div className="circle-deco cd-2"></div>

                <h3>Contact Information</h3>
                <p>Fill up the form and our team will get back to you within 24 hours.</p>

                <ul className="info-list">
                    <li className="info-item">
                        <i className="fa-solid fa-phone"></i>
                        <div>
                            <span>Phone</span>
                            <strong>+94 11 265 0301</strong>
                        </div>
                    </li>
                    <li className="info-item">
                        <i className="fa-solid fa-envelope"></i>
                        <div>
                            <span>Email</span>
                            <strong>info@reva.lk</strong>
                        </div>
                    </li>
                    <li className="info-item">
                        <i className="fa-solid fa-location-dot"></i>
                        <div>
                            <span>Location</span>
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

            <div className="contact-form-card">
                <div className="user-badge">
                    <i className="fa-solid fa-user-check"></i> Sending as: User Name
                </div>

                <form onSubmit={(e) => e.preventDefault()}>
                    <div className="form-group">
                        <label>Subject</label>
                        <select className="contact-input">
                            <option>General Inquiry</option>
                            <option>Report an Issue</option>
                            <option>Data Collaboration</option>
                            <option>Academic Research</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Message</label>
                        <textarea className="contact-input" placeholder="How can we help you?"></textarea>
                    </div>

                    <button type="submit" className="btn-primary" style={{width: '100%'}}>Send Message</button>
                </form>
            </div>
        </div>
        <Footer />
      </div>
    </Layout>
  );
};

export default Contact;