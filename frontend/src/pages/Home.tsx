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

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <rect width="100" height="100" fill="${bgColor}" />
      <text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" fill="#ffffff" font-family="sans-serif" font-size="40px" font-weight="bold">
        ${initials}
      </text>
    </svg>
  `;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

const Home: React.FC = () => {
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 768);
  
  // Check sessionStorage on initial load.
  const [isLoading, setIsLoading] = useState<boolean>(
    !sessionStorage.getItem('hasSeenHomeLoader')
  );
  
  // State for Mobile Horizontal Roadmap
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

  // Reviews state & Form state
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

  // Handle Loading Screen & Scroll Lock
  useEffect(() => {
    if (!isLoading) {
        document.body.style.overflow = 'auto';
        return;
    }

    if (isMobile) {
      document.body.style.overflow = 'hidden';
    }

    const timer = setTimeout(() => {
        setIsLoading(false);
        sessionStorage.setItem('hasSeenHomeLoader', 'true');
    }, 3000);

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
        <>
            {/* HERO SECTION */}
            <section className="section-card">
              <div className="hero-box">
                <div className="hero-text-content">
                  <h1 className="hero-title">Your Real Estate Virtual Assistant</h1>
                  <p className="hero-subtext">Start for free and get intelligent AI-driven insights for smarter property decisions.</p>
                  <Link to="/house-price" className="hero-cta-btn"><i className="fa-solid fa-bolt"></i> Explore AI Engine</Link>
                </div>
              </div>
            </section>

            {/* SERVICES SECTION */}
            <section className="section-card">
              <div className="section-header">
                <h2>Our Predictions Services</h2>
                <p>AI-driven predictions tailored to your real estate needs.</p>
              </div>
              <div className="prediction-cards-container">
                <div className="m-card-custom m-card-blue">
                  <div className="m-card-content">
                    <img src="/img/housing.png" alt="Housing" className="m-card-img" />
                    <h3>Housing Price Prediction</h3>
                    <p>Accurate price estimates for buying or selling houses using deep market data.</p>
                    <Link to="/house-price" className="btn-light">Explore <i className="fa-solid fa-arrow-right"></i></Link>
                  </div>
                </div>
                <div className="m-card-custom m-card-dark flex-row-reverse">
                  <div className="m-card-content">
                    <img src="/img/rentals.png" alt="Rentals" className="m-card-img" />
                    <h3>Rental Price Prediction</h3>
                    <p>Find fair rental rates for apartments, houses, and commercial properties.</p>
                    <Link to="/rental-price" className="btn-light">Explore <i className="fa-solid fa-arrow-right"></i></Link>
                  </div>
                </div>
                <div className="m-card-custom m-card-dark">
                  <div className="m-card-content">
                    <img src="/img/lands.png" alt="Lands" className="m-card-img" />
                    <h3>Land Price Prediction</h3>
                    <p>Evaluate land values based on location, zoning, and historical trends.</p>
                    <Link to="/land-price" className="btn-light">Explore <i className="fa-solid fa-arrow-right"></i></Link>
                  </div>
                </div>
              </div>
            </section>

            {/* HOW IT WORKS SECTION */}
            <section className="section-card bg-light">
              <div className="section-header">
                <h2>How Rēva Works</h2>
                <p>A simple, data-driven approach to real estate intelligence.</p>
              </div>
              
              <div className="m-roadmap-container">
                <div className="m-roadmap-content">
                  <div className="m-roadmap-step active">
                    <div className="m-roadmap-icon">
                      <img src={roadmapSteps[activeRoadmapStep].icon} alt={roadmapSteps[activeRoadmapStep].alt} />
                    </div>
                    <h3>{roadmapSteps[activeRoadmapStep].title}</h3>
                    <p>{roadmapSteps[activeRoadmapStep].text}</p>
                  </div>
                </div>

                <div className="m-roadmap-controls">
                  <button 
                    className="m-roadmap-btn" 
                    onClick={() => setActiveRoadmapStep((prev) => (prev > 0 ? prev - 1 : roadmapSteps.length - 1))}
                    aria-label="Previous step"
                  >
                    <i className="fa-solid fa-chevron-left"></i>
                  </button>
                  <div className="m-roadmap-indicators">
                    {roadmapSteps.map((_, idx) => (
                      <span 
                        key={idx} 
                        className={`m-indicator ${activeRoadmapStep === idx ? 'active' : ''}`}
                        onClick={() => setActiveRoadmapStep(idx)}
                      ></span>
                    ))}
                  </div>
                  <button 
                    className="m-roadmap-btn" 
                    onClick={() => setActiveRoadmapStep((prev) => (prev < roadmapSteps.length - 1 ? prev + 1 : 0))}
                    aria-label="Next step"
                  >
                    <i className="fa-solid fa-chevron-right"></i>
                  </button>
                </div>
              </div>
            </section>

            {/* REVIEWS SECTION (MOBILE) */}
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
        /* --- DESKTOP VIEW --- */
        <div className="home-container">
            {/* HERO SECTION */}
            <div className="hero-box-d">
                <div className="hero-content-d">
                    <h1 className="hero-title-d">Your Real Estate Virtual Assistant</h1>
                    <p className="hero-subtext-d">Start for free and get intelligent AI-driven insights for smarter property decisions.</p>
                    <Link to="/house-price" className="hero-cta-btn-d"><i className="fa-solid fa-bolt"></i> Explore AI Engine</Link>
                </div>
            </div>

            {/* SERVICES SECTION */}
            <section className="section-card">
                <div className="section-header">
                    <h2>Our Predictions Services</h2>
                    <p>AI-driven predictions tailored to your real estate needs.</p>
                </div>
                <div className="prediction-cards-container-d">
                    <div className="card-custom-d card-blue-d">
                        <div className="card-content-d">
                            <img src="/img/housing.png" alt="Housing" className="card-img-d" />
                            <h3>Housing Price Prediction</h3>
                            <p>Accurate price estimates for buying or selling houses using deep market data.</p>
                            <Link to="/house-price" className="btn-light">Explore <i className="fa-solid fa-arrow-right"></i></Link>
                        </div>
                    </div>
                    <div className="card-custom-d card-dark-d flex-row-reverse">
                        <div className="card-content-d">
                            <img src="/img/rentals.png" alt="Rentals" className="card-img-d" />
                            <h3>Rental Price Prediction</h3>
                            <p>Find fair rental rates for apartments, houses, and commercial properties.</p>
                            <Link to="/rental-price" className="btn-light">Explore <i className="fa-solid fa-arrow-right"></i></Link>
                        </div>
                    </div>
                    <div className="card-custom-d card-dark-d">
                        <div className="card-content-d">
                            <img src="/img/lands.png" alt="Lands" className="card-img-d" />
                            <h3>Land Price Prediction</h3>
                            <p>Evaluate land values based on location, zoning, and historical trends.</p>
                            <Link to="/land-price" className="btn-light">Explore <i className="fa-solid fa-arrow-right"></i></Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* HOW IT WORKS SECTION */}
            <section className="section-card bg-light">
                <div className="section-header">
                    <h2>How Rēva Works</h2>
                    <p>A simple, data-driven approach to real estate intelligence.</p>
                </div>
                <div className="steps-grid-d">
                    <div className="step-card-d">
                        <div className="step-icon-d"><img src="/img/icons/keyboard.svg" alt="Keyboard" /></div>
                        <h3>You Provide Details</h3>
                        <p>Enter property information such as location, type, and size. Rēva uses this context as the foundation for analysis.</p>
                    </div>
                    <div className="step-card-d">
                        <div className="step-icon-d"><img src="/img/icons/location.svg" alt="Location" /></div>
                        <h3>Location Intelligence</h3>
                        <p>Rēva evaluates accessibility, nearby cities, and urban influence to understand the real value of the location.</p>
                    </div>
                    <div className="step-card-d">
                        <div className="step-icon-d"><img src="/img/icons/aipowered.svg" alt="AI Powered" /></div>
                        <h3>AI-Powered Analysis</h3>
                        <p>Machine learning models analyze market trends and historical patterns to estimate realistic price ranges.</p>
                    </div>
                    <div className="step-card-d">
                        <div className="step-icon-d"><img src="/img/icons/insights.svg" alt="Insights" /></div>
                        <h3>Clear Insights</h3>
                        <p>Rēva presents understandable predictions and insights, helping you make confident real estate decisions.</p>
                    </div>
                </div>
            </section>

            {/* REVIEWS SECTION (DESKTOP) */}
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