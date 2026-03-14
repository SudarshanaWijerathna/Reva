import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';

const Home: React.FC = () => {
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // New State for Mobile Horizontal Roadmap
  const [activeRoadmapStep, setActiveRoadmapStep] = useState<number>(0);

  // Roadmap Data Array
  const roadmapSteps = [
    { icon: "/img/icons/keyboard.svg", alt: "Keyboard", title: "You Provide Details", text: "Enter property information such as location, type, and size. Rēva uses this context as the foundation for analysis." },
    { icon: "/img/icons/location.svg", alt: "Location", title: "Location Intelligence", text: "Rēva evaluates accessibility, nearby cities, and urban influence to understand the real value of the location." },
    { icon: "/img/icons/aipowered.svg", alt: "AI Powered", title: "AI-Powered Analysis", text: "Machine learning models analyze market trends and historical patterns to estimate realistic price ranges." },
    { icon: "/img/icons/insights.svg", alt: "Insights", title: "Clear Insights", text: "Rēva presents understandable predictions and insights, helping you make confident real estate decisions." } 
  ];

  // Mobile Review Carousel
  const [activeReviewIdx, setActiveReviewIdx] = useState<number>(0);

  const mobileReviews = [
    { name: "Sarah Perera", stars: 5, text: "Surprising accuracy for my plot in Kandy!", img: "https://i.pravatar.cc/150?img=68" },
    { name: "Nimal Fernando", stars: 5, text: "The rental predictions for Colombo 7 are spot on. Saved me a lot of time!", img: "https://i.pravatar.cc/150?img=11" },
    { name: "K. Jayasuriya", stars: 4, text: "Very helpful interface. Love how it maps the urban influence.", img: "https://i.pravatar.cc/150?img=32" },
    { name: "Amani Silva", stars: 5, text: "Used this to cross-check my property valuation. The AI is impressive.", img: "https://i.pravatar.cc/150?img=44" },
    { name: "Priyantha Liyanage", stars: 5, text: "Fantastic tool for quick insights. The privacy features are highly appreciated.", img: "https://i.pravatar.cc/150?img=15" },
    { name: "Dilini Perera", stars: 4, text: "Really smooth UI and the predictions are very close to market rates.", img: "https://i.pravatar.cc/150?img=5" }
  ];

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    
    // Exact Loader logic from index.html
    document.body.style.overflow = 'hidden';
    const timer = setTimeout(() => {
        setIsLoading(false);
        document.body.style.overflow = 'auto'; 
    }, 3000);

    return () => {
        window.removeEventListener('resize', handleResize);
        clearTimeout(timer);
        document.body.style.overflow = 'auto';
    };
  }, []);

  useEffect(() => {
    if (!isMobile) return;
    const interval = setInterval(() => {
      setActiveReviewIdx((prev) => (prev + 1) % mobileReviews.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [isMobile, mobileReviews.length]);

  return (
    <Layout>
      {/* Loader from index.html */}
      {isMobile && (
          <div className="loading-screen" id="revaLoader" style={{ opacity: isLoading ? 1 : 0, visibility: isLoading ? 'visible' : 'hidden' }}>
              <div className="loading-shape shape-1"><img src="/img/icons/dashboard.svg" alt="Dashboard" /></div>
              <div className="loading-shape shape-2"><img src="/img/icons/support.svg" alt="Support" /></div>
              <div className="loading-shape shape-3"><img src="/img/icons/prediction.svg" alt="Prediction" /></div>
              <div className="loading-shape shape-4"><img src="/img/icons/chat.svg" alt="Chat" /></div>

              <div className="loading-center">
                  <img src="/img/loading.gif" alt="reva-gif-image" className="loading-gif" />
                  <div className="loading-dots">
                      <span></span><span></span><span></span>
                  </div>
              </div>

              <div className="loading-bottom-text">
                  <h1>Your real estate virtual assistant</h1>
                  <p>Start for free and get intelligent AI-driven insights<br/> for smarter property decisions.</p>
              </div>
          </div>
      )}

      {isMobile ? (
        /* =========================================
           MOBILE VIEW (Exact match to index.html)
           ========================================= */
        <>
            <div className="mobile-welcome-banner">
                <section className="reva-hero-content">
                    <div className="reva-hero-text">
                        <h1>Rēva</h1>
                        <h1>Intelligent Real Estate Virtual Assistant</h1>
                    </div>
                    <div className="reva-hero-image">
                        <img src="/img/banner-hero-image.gif" alt="Rēva Assistant" className="overhang-image" />
                    </div>
                </section>
            </div>

            <div className="prediction-cards">
                <Link to="/house-price" className="prediction-card">
                    <div className="prediction-card-icon"><img src="/img/icons/house.svg" alt="Housing" /></div>
                    <div className="prediction-card-text">
                        <h3>Housing</h3>
                        <p>Predict accurate house prices using location, features, and market trends powered by machine learning.</p>
                    </div>
                </Link>
                <Link to="/rental-price" className="prediction-card">
                    <div className="prediction-card-icon"><img src="/img/icons/rental.svg" alt="Rentals" /></div>
                    <div className="prediction-card-text">
                        <h3>Rentals</h3>
                        <p>Estimate fair rental values instantly based on property details, accessibility, and demand patterns.</p>
                    </div>
                </Link>
                <Link to="/land-price" className="prediction-card">
                    <div className="prediction-card-icon"><img src="/img/icons/land.svg" alt="Lands" /></div>
                    <div className="prediction-card-text">
                        <h3>Lands</h3>
                        <p>Get data-driven land price predictions using location intelligence, road access, and urban influence.</p>
                    </div>
                </Link>
            </div>
            
            {/* UPDATED: Mobile How Rēva Works Section */}
            <section className="section-card bg-img how-works-section">
                <div className="section-header">
                    <h2>How Rēva Works</h2>
                    <p>Rēva combines user input, location intelligence, and machine learning to deliver reliable and transparent real estate insights.</p>
                </div>
                
                <div className="m-roadmap-wrapper">
                    <div className="m-roadmap-nav">
                        <div className="m-roadmap-line"></div>
                        {roadmapSteps.map((step, idx) => (
                            <div 
                                key={idx} 
                                className={`m-roadmap-step ${activeRoadmapStep === idx ? 'active' : ''}`}
                                onClick={() => setActiveRoadmapStep(idx)}
                            >
                                <div className="m-roadmap-icon">
                                    <img src={step.icon} alt={step.alt} />
                                </div>
                            </div>
                        ))}
                    </div>
                    
                    <div className="m-roadmap-content">
                        {/* The arrow indicator moves dynamically based on the active step */}
                        <div 
                            className="m-roadmap-arrow" 
                            style={{ left: `calc(14.5% + ${activeRoadmapStep * 23.5}%)` }}
                        ></div>
                        <h3>{roadmapSteps[activeRoadmapStep].title}</h3>
                        <p>{roadmapSteps[activeRoadmapStep].text}</p>
                    </div>
                </div>
            </section>

            <div className="intro-points">
                <p><i className="fa-solid fa-circle-check"></i> Rēva helps you understand and predict land, housing, and rental prices using AI-driven analysis of location, market trends, and historical data.</p>
                <p><i className="fa-solid fa-circle-check"></i> Unlock the power of AI to navigate the real estate market with confidence and make smarter decisions for your future.</p>
            </div>
            
            {/* UPDATED: Mobile Privacy Section with Custom SVGs */}
            <section className="section-card bg-white">
              <div className="m-split-layout">
                <h2>Your Data Stays With You</h2>
                <p>Rēva is designed with privacy at its core. Your inputs are used only for analysis, never for tracking.</p>
                
                <div className="m-trust-box">
                  <div className="m-trust-item">
                    <img src="/img/icons/personal.svg" alt="Personal Data" className="m-trust-icon" />
                    <span>No personal<br/>data shared</span>
                  </div>
                  <div className="m-trust-item">
                    <img src="/img/icons/secure.svg" alt="Secure Processing" className="m-trust-icon" />
                    <span>Secure<br/>processing</span>
                  </div>
                  <div className="m-trust-item">
                    <img src="/img/icons/tracking.svg" alt="No Tracking" className="m-trust-icon" />
                    <span>No hidden<br/>tracking</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="section-card bg-light">
              <div className="section-header">
                <h2>Community Feedback</h2>
                <p>See what others are saying about Rēva.</p>
              </div>

              <div className="m-feedback-grid">
                <div className="m-feedback-form-card">
                  <h4>Leave a Review</h4>
                  <textarea className="m-reva-input" placeholder="Your experience..."></textarea>
                  <div className="m-form-bottom-row">
                      <div className="m-star-rating">
                        <input type="radio" id="star5m" name="ratingm" value="5"/><label htmlFor="star5m">★</label>
                        <input type="radio" id="star4m" name="ratingm" value="4"/><label htmlFor="star4m">★</label>
                        <input type="radio" id="star3m" name="ratingm" value="3"/><label htmlFor="star3m">★</label>
                        <input type="radio" id="star2m" name="ratingm" value="2"/><label htmlFor="star2m">★</label>
                        <input type="radio" id="star1m" name="ratingm" value="1"/><label htmlFor="star1m">★</label>
                      </div>
                      <button className="m-btn-submit">Submit</button>
                  </div>
                </div>

                <div className="m-reviews-list">
                  {mobileReviews.map((review, idx) => (
                      <div key={idx} className={`m-review-card ${activeReviewIdx === idx ? 'active' : ''}`}>
                        <div className="m-review-avatar"><img src={review.img} alt={review.name} /></div>
                        <div className="m-review-content">
                          <div className="m-review-header">
                              <h4>{review.name}</h4>
                              <div className="m-review-stars">
                                  {[...Array(5)].map((_, starIdx) => (
                                      <i key={starIdx} className={starIdx < review.stars ? "fa-solid fa-star" : "fa-regular fa-star"}></i>
                                  ))}
                              </div>
                          </div>
                          <p>{review.text}</p>
                        </div>
                      </div>
                  ))}
                </div>
              </div>
            </section>
        </>
      ) : (
        /* =========================================
           DESKTOP VIEW (Remains robust)
           ========================================= */
        <div className="container">
            <div className="welcome-banner">
                <section className="reva-hero-content">
                    <div className="leftside-hero">
                        <h1>Rēva, <span> Intelligent Real Estate Virtual Assistant</span></h1>
                        <p>Rēva helps you understand and predict land, housing, and rental prices using AI-driven analysis of location, market trends, and historical data.</p>
                        <div className="reva-hero-features"></div>
                    </div>
                    <div className="rightside-hero">
                        <img src="/img/banner-hero-image.gif" alt="Real Estate Analysis Animation" />
                    </div>
                </section>
            </div>

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

            <section className="section-card bg-light">
                <div className="section-header">
                    <h2>How Rēva Works</h2>
                    <p>Rēva combines user input, location intelligence, and machine learning to deliver reliable and transparent real estate insights.</p>
                </div>
                <div className="how-reva-steps-desktop">
                    <div className="how-step-d">
                        <div className="step-icon-d"><i className="fa-solid fa-keyboard"></i></div>
                        <h3>You Provide Details</h3>
                        <p>Enter property information such as location, type, and size. Rēva uses this context as the foundation for analysis.</p>
                    </div>
                    <div className="how-step-d">
                        <div className="step-icon-d"><i className="fa-solid fa-map-location-dot"></i></div>
                        <h3>Location Intelligence</h3>
                        <p>Rēva evaluates accessibility, nearby cities, and urban influence to understand the real value of the location.</p>
                    </div>
                    <div className="how-step-d">
                        <div className="step-icon-d"><i className="fa-solid fa-brain"></i></div>
                        <h3>AI-Powered Analysis</h3>
                        <p>Machine learning models analyze market trends and historical patterns to estimate realistic price ranges.</p>
                    </div>
                    <div className="how-step-d">
                        <div className="step-icon-d"><i className="fa-solid fa-chart-simple"></i></div>
                        <h3>Clear Insights</h3>
                        <p>Rēva presents understandable predictions and insights, helping you make confident real estate decisions.</p>
                    </div>
                </div>
            </section>

            <section className="section-card bg-white">
                <div className="split-layout-d">
                    <div className="split-text-d">
                        <h2>Your Data Stays With You</h2>
                        <p>Rēva is designed with privacy at its core. Any information you provide is used only to generate predictions and insights — never for tracking, selling, or profiling.</p>
                        <ul className="trust-points-d">
                            <li><i className="fa-solid fa-user"></i> No personal data shared with third parties</li>
                            <li><i className="fa-solid fa-lock"></i> Inputs are processed securely</li>
                            <li><i className="fa-solid fa-shield-halved"></i> No hidden tracking</li>
                        </ul>
                    </div>
                    <div className="split-image-d trust-visuals-d">
                        <div className="trust-float-icon-d icon-user"><i className="fa-solid fa-user"></i></div>
                        <div className="trust-float-icon-d icon-shield"><i className="fa-solid fa-shield-halved"></i></div>
                        <div className="trust-float-icon-d icon-lock"><i className="fa-solid fa-lock"></i></div>
                        <img src="/img/privacy.png" alt="Data privacy illustration" className="trust-main-img-d" />
                    </div>
                </div>
            </section>

            <section className="section-card bg-light">
                <div className="section-header">
                    <h2>Community Feedback</h2>
                    <p>Help us improve Rēva by sharing your experience, or see what others are saying.</p>
                </div>
                <div className="feedback-grid-d">
                    <div className="feedback-form-card-d">
                        <h2>Leave a Review</h2>
                        <p>How accurate were the predictions?</p>
                        <form onSubmit={(e) => e.preventDefault()}>
                            <div className="star-rating-d">
                                <input type="radio" id="star5" name="rating" value="5" /><label htmlFor="star5" title="5 stars">★</label>
                                <input type="radio" id="star4" name="rating" value="4" /><label htmlFor="star4" title="4 stars">★</label>
                                <input type="radio" id="star3" name="rating" value="3" /><label htmlFor="star3" title="3 stars">★</label>
                                <input type="radio" id="star2" name="rating" value="2" /><label htmlFor="star2" title="2 stars">★</label>
                                <input type="radio" id="star1" name="rating" value="1" /><label htmlFor="star1" title="1 star">★</label>
                            </div>
                            <div className="form-group-d">
                                <label>Your Comment</label>
                                <textarea className="reva-input-d" placeholder="Tell us about your experience with Rēva..."></textarea>
                            </div>
                            <button type="submit" className="btn-primary" style={{width: '100%'}}>Submit Review</button>
                        </form>
                    </div>

                    <div className="reviews-list-d">
                        <div className="review-card-d">
                            <div className="review-avatar-d"><img src="https://i.pravatar.cc/150?img=68" alt="User Avatar" /></div>
                            <div className="review-content-d">
                                <h4>Sarah Perera</h4>
                                <div className="review-stars-d">
                                    <i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i>
                                </div>
                                <p>I was surprised by how accurate the land prediction was for my plot in Kandy. It matched the bank valuation almost perfectly.</p>
                            </div>
                        </div>
                        <div className="review-card-d">
                            <div className="review-avatar-d"><img src="https://i.pravatar.cc/150?img=11" alt="User Avatar" /></div>
                            <div className="review-content-d">
                                <h4>Kamal De Silva</h4>
                                <div className="review-stars-d">
                                    <i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-regular fa-star"></i>
                                </div>
                                <p>Great tool for getting a quick rental estimate. The interface is very clean and easy to use.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
      )}
    </Layout>
  );
};

export default Home;