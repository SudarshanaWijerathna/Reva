import React from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import Footer from '../components/Footer';

const Home: React.FC = () => {
  return (
    <Layout>
      <div className="container">
        
        {/* HERO SECTION */}
        <div className="welcome-banner">
            <section className="reva-hero-content">
                <div className="leftside-hero">
                    <h1>Rēva, <span> Intelligent Real Estate Virtual Assistant</span></h1>
                    <p>Reva helps you understand and predict land, housing, and rental prices using AI-driven analysis of location, market trends, and historical data.</p>
                
                    <div className="reva-hero-features">
                        {/* Features can be added here if needed */}
                    </div>
                </div>

                <div className="rightside-hero">
                    <img src="/img/banner-hero-image.gif" alt="Real Estate Analysis Animation" />
                </div>
            </section>
        </div>

        {/* NAVIGATION CARDS */}
        <div className="banner-cards">
            <Link to="/house-price" className="assistant-card">
                <div className="assistant-header">
                    <img src="/img/housing.png" alt="Housing" />
                    <div className="assistant-text">
                        <h2>Housing</h2>
                        <p>Predict accurate house prices using location, features, and market trends powered by machine learning.</p>
                    </div>
                </div>
            </Link>

            <Link to="/rental-price" className="assistant-card">
                <div className="assistant-header">
                    <img src="/img/rentals.png" alt="Rentals" />
                    <div className="assistant-text">
                        <h2>Rentals</h2>
                        <p>Estimate fair rental values instantly based on property details, accessibility, and demand patterns.</p>
                    </div>
                </div>
            </Link>

            <Link to="/land-price" className="assistant-card">
                <div className="assistant-header">
                    <img src="/img/lands.png" alt="Lands" />
                    <div className="assistant-text">
                        <h2>Lands</h2>
                        <p>Get data-driven land price predictions using location intelligence, road access, and urban influence.</p>
                    </div>
                </div>
            </Link>
        </div>

        {/* HOW IT WORKS */}
        <section className="section-card bg-light">
            <div className="section-header">
                <h2>How Reva Works</h2>
                <p>Reva combines user input, location intelligence, and machine learning to deliver reliable and transparent real estate insights.</p>
            </div>

            <div className="how-reva-steps">
                <div className="how-step">
                    <div className="step-icon"><i className="fa-solid fa-keyboard"></i></div>
                    <h3>You Provide Details</h3>
                    <p>Enter property information such as location, type, and size. Reva uses this context as the foundation for analysis.</p>
                </div>
                <div className="how-step">
                    <div className="step-icon"><i className="fa-solid fa-map-location-dot"></i></div>
                    <h3>Location Intelligence</h3>
                    <p>Reva evaluates accessibility, nearby cities, and urban influence to understand the real value of the location.</p>
                </div>
                <div className="how-step">
                    <div className="step-icon"><i className="fa-solid fa-brain"></i></div>
                    <h3>AI-Powered Analysis</h3>
                    <p>Machine learning models analyze market trends and historical patterns to estimate realistic price ranges.</p>
                </div>
                <div className="how-step">
                    <div className="step-icon"><i className="fa-solid fa-chart-simple"></i></div>
                    <h3>Clear Insights</h3>
                    <p>Reva presents understandable predictions and insights, helping you make confident real estate decisions.</p>
                </div>
            </div>
        </section>

        {/* PRIVACY SECTION */}
        <section className="section-card bg-white">
            <div className="split-layout">
                <div className="split-text">
                    <h2>Your Data Stays With You</h2>
                    <p>Reva is designed with privacy at its core. Any information you provide is used only to generate predictions and insights — never for tracking, selling, or profiling.</p>
                    <ul className="trust-points">
                        <li><i className="fa-solid fa-user"></i> No personal data shared with third parties</li>
                        <li><i className="fa-solid fa-lock"></i> Inputs are processed securely</li>
                        <li><i className="fa-solid fa-shield-halved"></i> No hidden tracking</li>
                    </ul>
                </div>
                
                <div className="split-image trust-visuals">
                    <div className="trust-float-icon icon-user">
                        <i className="fa-solid fa-user"></i>
                    </div>
                    <div className="trust-float-icon icon-shield">
                        <i className="fa-solid fa-shield-halved"></i>
                    </div>
                    <div className="trust-float-icon icon-lock">
                        <i className="fa-solid fa-lock"></i>
                    </div>
                    <img src="/img/privacy.png" alt="Data privacy illustration" className="trust-main-img" />
                </div>
            </div>
        </section>

        {/* FEEDBACK SECTION */}
        <section className="section-card bg-light">
            <div className="section-header">
                <h2>Community Feedback</h2>
                <p>Help us improve Reva by sharing your experience, or see what others are saying.</p>
            </div>

            <div className="feedback-grid">
                
                <div className="feedback-form-card">
                    <h2>Leave a Review</h2>
                    <p>How accurate were the predictions?</p>
                    
                    <form onSubmit={(e) => e.preventDefault()}>
                        <div className="star-rating">
                            <input type="radio" id="star5" name="rating" value="5" /><label htmlFor="star5" title="5 stars">★</label>
                            <input type="radio" id="star4" name="rating" value="4" /><label htmlFor="star4" title="4 stars">★</label>
                            <input type="radio" id="star3" name="rating" value="3" /><label htmlFor="star3" title="3 stars">★</label>
                            <input type="radio" id="star2" name="rating" value="2" /><label htmlFor="star2" title="2 stars">★</label>
                            <input type="radio" id="star1" name="rating" value="1" /><label htmlFor="star1" title="1 star">★</label>
                        </div>

                        <div className="form-group">
                            <label>Your Comment</label>
                            <textarea className="reva-input" placeholder="Tell us about your experience with Reva..."></textarea>
                        </div>

                        <button type="submit" className="btn-primary" style={{width: '100%'}}>Submit Review</button>
                    </form>
                </div>

                <div className="reviews-list">
                    <div className="review-card">
                        <div className="review-avatar">
                            <img src="https://i.pravatar.cc/150?img=68" alt="User Avatar" />
                        </div>
                        <div className="review-content">
                            <h4>Sarah Perera</h4>
                            <div className="review-stars">
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                            </div>
                            <p>I was surprised by how accurate the land prediction was for my plot in Kandy. It matched the bank valuation almost perfectly.</p>
                        </div>
                    </div>

                    <div className="review-card">
                        <div className="review-avatar">
                            <img src="https://i.pravatar.cc/150?img=12" alt="User Avatar" />
                        </div>
                        <div className="review-content">
                            <h4>Kamal De Silva</h4>
                            <div className="review-stars">
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-regular fa-star"></i>
                            </div>
                            <p>Great tool for getting a quick rental estimate. The interface is very clean and easy to use.</p>
                        </div>
                    </div>

                    <div className="review-card">
                        <div className="review-avatar">
                            <img src="https://i.pravatar.cc/150?img=33" alt="User Avatar" />
                        </div>
                        <div className="review-content">
                            <h4>Nimali Fernando</h4>
                            <div className="review-stars">
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star"></i>
                                <i className="fa-solid fa-star-half-stroke"></i>
                            </div>
                            <p>Used this for my final year research comparison. The location intelligence data is surprisingly deep.</p>
                        </div>
                    </div>

                </div>
            </div>
        </section>

        <Footer />
      </div>
    </Layout>
  );
};

export default Home;