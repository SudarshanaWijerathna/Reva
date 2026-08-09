import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import '../assets/css/navbar.css';
import { API_BASE_URL } from '../config/api';

interface ReviewItem {
  id: number;
  name: string;
  email: string;
  rating: number;
  comment: string;
  avatar_url?: string | null;
  created_at?: string;
}

// Initials Avatar generator
const generateInitialsAvatar = (name: string): string => {
  const initials = (name || '')
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'U';

  const colors = ['#4445ff', '#00C897', '#fbbf24', '#e11d48', '#9c27b0'];
  const charCode = (name || '').charCodeAt(0) || 0;
  const bgColor = colors[charCode % colors.length];

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="${bgColor}"/><text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-size="40px" font-weight="bold">${initials}</text></svg>`;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};


const Home: React.FC = () => {
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);
  
  // 1. FIX: Check sessionStorage on initial load. If 'hasSeenHomeLoader' exists, start as FALSE.
  const [isLoading, setIsLoading] = useState<boolean>(
    !sessionStorage.getItem('hasSeenHomeLoader')
  );
  
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

  // Dynamic Reviews & Form state
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [reviewRating, setReviewRating] = useState<number>(5);
  const [reviewComment, setReviewComment] = useState<string>('');
  const [guestName, setGuestName] = useState<string>('');
  const [guestEmail, setGuestEmail] = useState<string>('');

  // Check auth state
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  const userEmail = localStorage.getItem('user_email') || sessionStorage.getItem('user_email');
  const isLoggedIn = !!token && !!userEmail;

  const fetchReviews = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/reviews`);
      if (res.ok) {
        const data = await res.json();
        setReviews(data);
      }
    } catch (err) {
      console.error('Error fetching reviews:', err);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewComment.trim()) return;

    if (!isLoggedIn && (!guestName.trim() || !guestEmail.trim())) {
      alert('Please provide your name and email to submit a review.');
      return;
    }

    setIsSubmittingReview(true);
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/reviews`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          name: guestName,
          email: guestEmail,
          rating: reviewRating,
          comment: reviewComment,
        }),
      });

      if (res.ok) {
        setReviewComment('');
        setGuestName('');
        setGuestEmail('');
        setReviewRating(5);
        await fetchReviews();
      } else {
        const errData = await res.json();
        alert(errData.detail || 'Failed to submit review');
      }
    } catch (err) {
      console.error('Submit review error:', err);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  // Handle Window Resizing
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 2. FIX: Handle Loading Screen & Scroll Lock with 3-second timer
  useEffect(() => {
    // If the user has already seen the loader, ensure scrolling is unlocked and do nothing else
    if (!isLoading) {
        document.body.style.overflow = 'auto';
        return;
    }

    // Lock the scroll while the loader is showing on mobile
    if (isMobile) {
      document.body.style.overflow = 'hidden';
    }

    // Set the timer to clear the loading state after 3000ms (3 seconds)
    const timer = setTimeout(() => {
        setIsLoading(false);
        // Leave a breadcrumb so they don't see it again this session!
        sessionStorage.setItem('hasSeenHomeLoader', 'true');
    }, 3000);

    // Cleanup function in case the user navigates away before the timer finishes
    return () => {
        clearTimeout(timer);
        document.body.style.overflow = 'auto';
    };
  }, [isMobile, isLoading]);

  useEffect(() => {
    if (!isMobile || reviews.length === 0) return;
    const interval = setInterval(() => {
      setActiveReviewIdx((prev) => (prev + 1) % reviews.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [isMobile, reviews.length]);

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
                        <video
                          className="overhang-image hero-theme-media hero-theme-media-light"
                          autoPlay
                          muted
                          loop
                          playsInline
                        >
                          <source src="/img/animate_logo_light.webm" type="video/webm" />
                        </video>
                        <video
                          className="overhang-image hero-theme-media hero-theme-media-dark"
                          autoPlay
                          muted
                          loop
                          playsInline
                        >
                          <source src="/img/animate_logo_dark.webm" type="video/webm" />
                        </video>
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
                  <form onSubmit={handleReviewSubmit}>
                    {!isLoggedIn && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '10px' }}>
                        <input
                          type="text"
                          className="m-reva-input"
                          style={{ height: '36px', padding: '0 12px' }}
                          placeholder="Your Name"
                          value={guestName}
                          onChange={(e) => setGuestName(e.target.value)}
                          required
                        />
                        <input
                          type="email"
                          className="m-reva-input"
                          style={{ height: '36px', padding: '0 12px' }}
                          placeholder="Your Email"
                          value={guestEmail}
                          onChange={(e) => setGuestEmail(e.target.value)}
                          required
                        />
                      </div>
                    )}
                    <textarea
                      className="m-reva-input"
                      placeholder="Your experience..."
                      value={reviewComment}
                      onChange={(e) => setReviewComment(e.target.value)}
                      required
                    ></textarea>
                    <div className="m-form-bottom-row" style={{ marginTop: '10px' }}>
                      <div className="m-star-rating">
                        {[5, 4, 3, 2, 1].map((star) => (
                          <React.Fragment key={star}>
                            <input
                              type="radio"
                              id={`star${star}m`}
                              name="ratingm"
                              value={star}
                              checked={reviewRating === star}
                              onChange={() => setReviewRating(star)}
                            />
                            <label htmlFor={`star${star}m`}>★</label>
                          </React.Fragment>
                        ))}
                      </div>
                      <button type="submit" className="m-btn-submit" disabled={isSubmittingReview}>
                        {isSubmittingReview ? 'Submitting...' : 'Submit'}
                      </button>
                    </div>
                  </form>
                </div>

                <div className="m-reviews-list">
                  {reviews.length === 0 ? (
                    <div style={{ padding: '15px', color: 'var(--text-gray)', fontSize: '13px' }}>
                      No reviews yet. Be the first to leave a review!
                    </div>
                  ) : (
                    reviews.map((review, idx) => (
                      <div
                        key={review.id}
                        className={`m-review-card ${activeReviewIdx === idx ? 'active' : ''}`}
                      >
                        <div className="m-review-avatar">
                          <img
                            src={review.avatar_url || generateInitialsAvatar(review.name)}
                            alt={review.name}
                          />
                        </div>
                        <div className="m-review-content">
                          <div className="m-review-header">
                            <h4>{review.name}</h4>
                            <div className="m-review-stars">
                              {[...Array(5)].map((_, starIdx) => (
                                <i
                                  key={starIdx}
                                  className={starIdx < review.rating ? 'fa-solid fa-star' : 'fa-regular fa-star'}
                                ></i>
                              ))}
                            </div>
                          </div>
                          <p>{review.comment}</p>
                        </div>
                      </div>
                    ))
                  )}
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
                        <video
                          className="hero-theme-media hero-theme-media-light"
                          autoPlay
                          muted
                          loop
                          playsInline
                          aria-label="Real estate analysis animation light mode"
                        >
                          <source src="/img/animate_logo_light.webm" type="video/webm" />
                        </video>
                        <video
                          className="hero-theme-media hero-theme-media-dark"
                          autoPlay
                          muted
                          loop
                          playsInline
                          aria-label="Real estate analysis animation dark mode"
                        >
                          <source src="/img/animate_logo_dark.webm" type="video/webm" />
                        </video>
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
                        <form onSubmit={handleReviewSubmit}>
                            {!isLoggedIn && (
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '15px' }}>
                                <div className="form-group-d" style={{ marginBottom: 0 }}>
                                  <label>Your Name</label>
                                  <input
                                    type="text"
                                    className="reva-input-d"
                                    placeholder="John Doe"
                                    value={guestName}
                                    onChange={(e) => setGuestName(e.target.value)}
                                    required
                                  />
                                </div>
                                <div className="form-group-d" style={{ marginBottom: 0 }}>
                                  <label>Your Email</label>
                                  <input
                                    type="email"
                                    className="reva-input-d"
                                    placeholder="john@example.com"
                                    value={guestEmail}
                                    onChange={(e) => setGuestEmail(e.target.value)}
                                    required
                                  />
                                </div>
                              </div>
                            )}
                            <div className="star-rating-d">
                                {[5, 4, 3, 2, 1].map((star) => (
                                  <React.Fragment key={star}>
                                    <input
                                      type="radio"
                                      id={`star${star}`}
                                      name="rating"
                                      value={star}
                                      checked={reviewRating === star}
                                      onChange={() => setReviewRating(star)}
                                    />
                                    <label htmlFor={`star${star}`} title={`${star} stars`}>★</label>
                                  </React.Fragment>
                                ))}
                            </div>
                            <div className="form-group-d">
                                <label>Your Comment</label>
                                <textarea
                                  className="reva-input-d"
                                  placeholder="Tell us about your experience with Rēva..."
                                  value={reviewComment}
                                  onChange={(e) => setReviewComment(e.target.value)}
                                  required
                                ></textarea>
                            </div>
                            <button type="submit" className="btn-primary" style={{width: '100%'}} disabled={isSubmittingReview}>
                              {isSubmittingReview ? 'Submitting...' : 'Submit Review'}
                            </button>
                        </form>
                    </div>

                    <div className="reviews-list-d" style={{ maxHeight: '520px', overflowY: 'auto', paddingRight: '6px' }}>
                        {reviews.length === 0 ? (
                          <div style={{ padding: '24px', color: 'var(--text-gray)', background: '#fff', borderRadius: '20px' }}>
                            No reviews yet. Be the first to leave a review!
                          </div>
                        ) : (
                          reviews.map((review) => (
                            <div className="review-card-d" key={review.id}>
                              <div className="review-avatar-d">
                                <img
                                  src={review.avatar_url || generateInitialsAvatar(review.name)}
                                  alt={`${review.name} Avatar`}
                                />
                              </div>
                              <div className="review-content-d">
                                <h4>{review.name}</h4>
                                <div className="review-stars-d">
                                  {[...Array(5)].map((_, starIdx) => (
                                    <i
                                      key={starIdx}
                                      className={starIdx < review.rating ? "fa-solid fa-star" : "fa-regular fa-star"}
                                    ></i>
                                  ))}
                                </div>
                                <p>{review.comment}</p>
                              </div>
                            </div>
                          ))
                        )}
                    </div>
                </div>
            </section>
        </div>
      )}
    </Layout>
  );
};

export default Home;