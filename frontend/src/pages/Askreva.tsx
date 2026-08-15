import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import '../assets/css/askreva.css'; 
import { API_BASE_URL } from '../config/api';
import { useAuth } from '../context/AuthContext';

// --- HELPER FUNCTION: Auto-generate Initials Avatar ---
const generateInitialsAvatar = (name: string): string => {
  const initials = name
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || 'U';

  const colors = ['#4445ff', '#00C897', '#fbbf24', '#e11d48', '#9c27b0'];
  const charCode = name.charCodeAt(0) || 0;
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

type BrowserSpeechRecognition = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: (() => void) | null;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: (() => void) | null;
};

declare global {
  interface Window {
    SpeechRecognition?: new () => BrowserSpeechRecognition;
    webkitSpeechRecognition?: new () => BrowserSpeechRecognition;
  }
}

// --- Interfaces ---
interface ExtraData {
  model_type?: 'house' | 'land' | 'rental';
  property_type?: 'housing' | 'rental' | 'land' | string;
  extracted?: {
    district?: string;
    sub_location?: string;
    area?: string;
    location_text?: string;
    location?: string;
    size?: string;
    land_size?: string;
    house_size_sqft?: string;
    land_size_perches?: string;
    house_sqft?: string;
    land_perches?: string;
    bedrooms?: string;
    bathrooms?: string;
    quality_tier?: string;
    road_width_ft?: string;
    road?: string;
    road_access?: string;
    zoning_type?: string;
    utilities?: string;
    facilities?: string;
    property_type?: string;
    furnishing_status?: string;
    distance_to_town_m?: string;
    purchase_price?: string;
    purchase_date?: string;
    floors?: string;
    built_year?: string;
    property_condition?: string;
    monthly_rent?: string;
    occupancy_status?: string;
    lease_start_date?: string;
    lease_end_date?: string;
    tenant_type?: string;
  };
  price?: string;
  purchase_price?: string;
  range?: string;
  unit?: string;
  total_value?: string;
  confidence?: 'high' | 'medium' | 'low' | string;
  lstm_sequence?: number[];
  lstm_labels?: string[];
  rl_recommendation?: string;
  reasoning?: string;
  location?: string;
  features?: Record<string, any>;
  details?: Record<string, any>;
  summary?: {
    portfolio_value: number;
    total_investment: number;
    growth_percentage: number;
    total_profit: number;
    property_mix: { housing: number; rental: number; land: number };
    sentiment: string;
  };
  properties?: Array<{
    property_id: number;
    type: 'housing' | 'rental' | 'land';
    location: string;
    purchase_price: number;
    current_value: number;
    profit: number;
    sentiment: string;
    status: string;
    created_at: string;
    details?: Record<string, any>;
  }>;
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'reva';
  type: 'text' | 'prediction_form' | 'prediction_result' | 'full_analysis' | 'graph' | 'add_property_form' | 'portfolio_overview' | 'add_property_success';
  model_type?: 'house' | 'land' | 'rental';
  extraData?: ExtraData;
}


const SQFT_PER_PERCHE = 272.25;

const LOCATION_OPTIONS = [
  { label: 'Piliyandala', district: 'Colombo', lat: 6.801757, lon: 79.922731 },
  { label: 'Talawatugoda', district: 'Colombo', lat: 6.875865, lon: 79.939194 },
  { label: 'Malabe', district: 'Colombo', lat: 6.906079, lon: 79.969628 },
  { label: 'Athurugiriya', district: 'Colombo', lat: 6.872319, lon: 80.000388 },
  { label: 'Nugegoda', district: 'Colombo', lat: 6.864908, lon: 79.899679 },
  { label: 'Kottawa', district: 'Colombo', lat: 6.841165, lon: 79.965432 },
  { label: 'Homagama', district: 'Colombo', lat: 6.843276, lon: 80.003183 },
  { label: 'Battaramulla', district: 'Colombo', lat: 6.898382, lon: 79.917841 },
  { label: 'Dehiwala', district: 'Colombo', lat: 6.830119, lon: 79.880083 },
  { label: 'Maharagama', district: 'Colombo', lat: 6.8478, lon: 79.921762 },
  { label: 'Moratuwa', district: 'Colombo', lat: 6.788071, lon: 79.891281 },
  { label: 'Negombo', district: 'Gampaha', lat: 7.195547, lon: 79.857338 },
  { label: 'Kadawatha', district: 'Gampaha', lat: 7.004672, lon: 79.9542 },
  { label: 'Ja-Ela', district: 'Gampaha', lat: 7.08576, lon: 79.925444 },
  { label: 'Wattala', district: 'Gampaha', lat: 6.986013, lon: 79.907016 },
  { label: 'Gampaha City', district: 'Gampaha', lat: 7.084048, lon: 80.009831 },
  { label: 'Kiribathgoda', district: 'Gampaha', lat: 7.129421, lon: 80.02235 },
  { label: 'Ragama', district: 'Gampaha', lat: 7.023177, lon: 79.907772 },
  { label: 'Panadura', district: 'Kalutara', lat: 6.752799, lon: 79.894931 },
  { label: 'Horana', district: 'Kalutara', lat: 6.724653, lon: 80.039946 },
  { label: 'Bandaragama', district: 'Kalutara', lat: 6.714407, lon: 79.98906 },
  { label: 'Kalutara City', district: 'Kalutara', lat: 6.585395, lon: 79.96074 },
  { label: 'Wadduwa', district: 'Kalutara', lat: 6.636282, lon: 79.952845 },
  { label: 'Matugama', district: 'Kalutara', lat: 6.521943, lon: 80.113685 },
];

// --- 1. HOUSE PREDICTION FORM CARD (3 Steps) ---
const HousePredictionFormCard: React.FC<{ data: ExtraData; onSubmit: (prompt: string) => void }> = ({ data, onSubmit }) => {
  const [step, setStep] = useState(1);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const ex = data.extracted || {};

  const [form, setForm] = useState({
    house_sqft: ex.house_sqft || '1800',
    land_perches: ex.land_perches || '10',
    bedrooms: ex.bedrooms || '3',
    bathrooms: ex.bathrooms || '2',
    district: ex.district && ['Colombo', 'Gampaha', 'Kalutara'].includes(ex.district) ? ex.district : 'Colombo',
    sub_location: ex.sub_location || 'Moratuwa',
    market_period: '2025 H2',
    quality_tier: ex.quality_tier || 'normal',
    road_width_ft: ex.road_width_ft || '15',
    parking_spaces: '2',
    water: Boolean((ex.facilities || '').includes('water')),
    electricity: ex.facilities ? Boolean(ex.facilities.includes('electricity')) : true,
    main_road: Boolean((ex.facilities || '').includes('main_road')),
    air_conditioned: Boolean((ex.facilities || '').includes('air_conditioned')),
    cctv: Boolean((ex.facilities || '').includes('cctv')),
    garden: Boolean((ex.facilities || '').includes('garden')),
    fully_furnished: Boolean((ex.facilities || '').includes('fully_furnished')),
    hot_water: Boolean((ex.facilities || '').includes('hot_water')),
  });


  const locationOptions = LOCATION_OPTIONS.filter(l => l.district === form.district);
  const selectedLocation = locationOptions.find(l => l.label.toLowerCase() === form.sub_location.toLowerCase()) || locationOptions[0] || LOCATION_OPTIONS[0];

  const handleSubmit = () => {
    setIsSubmitted(true);
    const payload = {
      house_sqft: Number(form.house_sqft) || 1800,
      land_sqft: (Number(form.land_perches) || 10) * SQFT_PER_PERCHE,
      bedrooms: Number(form.bedrooms) || 3,
      bathrooms: Number(form.bathrooms) || 2,
      lat: selectedLocation.lat,
      lon: selectedLocation.lon,
      district: form.district,
      sub_location: selectedLocation.label,
      posted_year: 2025,
      posted_month: 12,
      quality_tier: form.quality_tier,
      road_width_ft: Number(form.road_width_ft) || 15,
      parking_spaces: Number(form.parking_spaces) || 2,
      water: form.water,
      electricity: form.electricity,
      main_road: form.main_road,
      air_conditioned: form.air_conditioned,
      cctv: form.cctv,
      garden: form.garden,
      fully_furnished: form.fully_furnished,
      hot_water: form.hot_water,
    };
    onSubmit(`[RUN_ESTIMATE] | house | ${JSON.stringify(payload)}`);
  };

  return (
    <div className="bubble">
      <div className="form-step-header">
        <div className="form-step-title">
          <i className="fa-solid fa-house" style={{ marginRight: '6px' }}></i> House Valuation Form
        </div>
        <div className="form-step-dots">
          <div className={`form-dot ${step === 1 ? 'active' : step > 1 ? 'completed' : ''}`}></div>
          <div className={`form-dot ${step === 2 ? 'active' : step > 2 ? 'completed' : ''}`}></div>
          <div className={`form-dot ${step === 3 ? 'active' : ''}`}></div>
        </div>
      </div>
      <p style={{ fontSize: '12px', color: 'var(--text-gray)', margin: '4px 0 10px 0' }}>
        Step {step} of 3: {step === 1 ? 'Property Sizing & Rooms' : step === 2 ? 'Location & Tier' : 'Facilities & Road Access'}
      </p>
      <hr className="chat-divider" />

      {/* Step 1 */}
      <div className={`form-step form-step-1 ${step === 1 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="input-group">
                <label>House Size (sqft)</label>
                <input type="number" className="input-field" value={form.house_sqft} onChange={e => setForm({...form, house_sqft: e.target.value})} disabled={isSubmitted} placeholder="e.g. 1800" />
              </div>
              <div className="input-group">
                <label>Land (perches)</label>
                <input type="number" className="input-field" value={form.land_perches} onChange={e => setForm({...form, land_perches: e.target.value})} disabled={isSubmitted} placeholder="e.g. 10" />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="input-group">
                <label>Bedrooms</label>
                <input type="number" className="input-field" value={form.bedrooms} onChange={e => setForm({...form, bedrooms: e.target.value})} disabled={isSubmitted} min="1" max="15" />
              </div>
              <div className="input-group">
                <label>Bathrooms</label>
                <input type="number" className="input-field" value={form.bathrooms} onChange={e => setForm({...form, bathrooms: e.target.value})} disabled={isSubmitted} min="1" max="10" />
              </div>
            </div>
            <button className="cta-btn" onClick={() => setStep(2)} disabled={isSubmitted}>Next: Location &nbsp;<i className="fa-solid fa-arrow-right"></i></button>
          </div>
        </div>
      </div>

      {/* Step 2 */}
      <div className={`form-step form-step-2 ${step === 2 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div className="input-group">
              <label>District</label>
              <select className="input-field" value={form.district} onChange={e => setForm({...form, district: e.target.value, sub_location: ''})} disabled={isSubmitted}>
                <option value="Colombo">Colombo</option>
                <option value="Gampaha">Gampaha</option>
                <option value="Kalutara">Kalutara</option>
              </select>
            </div>
            <div className="input-group">
              <label>Nearest Town / Area</label>
              <select className="input-field" value={form.sub_location} onChange={e => setForm({...form, sub_location: e.target.value})} disabled={isSubmitted}>
                {locationOptions.map(l => (
                  <option key={l.label} value={l.label}>{l.label}</option>
                ))}
              </select>
            </div>
            <div className="input-group">
              <label>House Type / Quality Tier</label>
              <select className="input-field" value={form.quality_tier} onChange={e => setForm({...form, quality_tier: e.target.value})} disabled={isSubmitted}>
                <option value="normal">Normal Residential</option>
                <option value="semi_luxury">Semi Luxury</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn-outline" onClick={() => setStep(1)} style={{ flex: 1 }} disabled={isSubmitted}>Back</button>
              <button className="cta-btn" onClick={() => setStep(3)} style={{ flex: 2 }} disabled={isSubmitted}>Next: Facilities &nbsp;<i className="fa-solid fa-arrow-right"></i></button>
            </div>
          </div>
        </div>
      </div>

      {/* Step 3 */}
      <div className={`form-step form-step-3 ${step === 3 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div className="input-group">
              <label>Facilities & Features</label>
              <div className="checkbox-grid">
                <label className="checkbox-item"><input type="checkbox" checked={form.water} onChange={e => setForm({...form, water: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Water</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.electricity} onChange={e => setForm({...form, electricity: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Electricity</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.main_road} onChange={e => setForm({...form, main_road: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Main road</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.air_conditioned} onChange={e => setForm({...form, air_conditioned: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> A/C</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.cctv} onChange={e => setForm({...form, cctv: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> CCTV</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.garden} onChange={e => setForm({...form, garden: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Garden</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.fully_furnished} onChange={e => setForm({...form, fully_furnished: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Furnished</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.hot_water} onChange={e => setForm({...form, hot_water: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Hot water</label>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="input-group">
                <label>Road Width (ft)</label>
                <input type="number" className="input-field" value={form.road_width_ft} onChange={e => setForm({...form, road_width_ft: e.target.value})} disabled={isSubmitted} />
              </div>
              <div className="input-group">
                <label>Parking Spaces</label>
                <input type="number" className="input-field" value={form.parking_spaces} onChange={e => setForm({...form, parking_spaces: e.target.value})} disabled={isSubmitted} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn-outline" onClick={() => setStep(2)} style={{ flex: 1 }} disabled={isSubmitted}>Back</button>
              <button className="cta-btn" onClick={handleSubmit} style={{ flex: 2 }} disabled={isSubmitted}>
                {isSubmitted ? <><i className="fa-solid fa-check"></i> Estimated</> : <><i className="fa-solid fa-calculator"></i> Estimate House Price</>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- 2. LAND PREDICTION FORM CARD (2 Steps) ---
const LandPredictionFormCard: React.FC<{ data: ExtraData; onSubmit: (prompt: string) => void }> = ({ data, onSubmit }) => {
  const [step, setStep] = useState(1);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const ex = data.extracted || {};

  const [form, setForm] = useState({
    land_size: ex.land_size || ex.size || '15',
    district: ex.district && ['Colombo', 'Gampaha', 'Kandy', 'Galle'].includes(ex.district) ? ex.district : 'Colombo',
    location_text: ex.location_text || ex.area || 'Maharagama',
    distance_to_town_m: ex.distance_to_town_m || '400',
    main_road: Boolean((ex.utilities || '').includes('Main road')),
    electricity: ex.utilities ? Boolean(ex.utilities.includes('Electricity')) : true,
    clear_deed: ex.utilities ? Boolean(ex.utilities.includes('Clear deed')) : true,
    water: ex.utilities ? Boolean(ex.utilities.includes('Water')) : true,
    bank_loan: Boolean((ex.utilities || '').includes('Bank loan')),
    near_town: ex.utilities ? Boolean(ex.utilities.includes('Near town')) : true,
    period: '2025 H2',
  });


  const handleSubmit = () => {
    setIsSubmitted(true);
    const payload = {
      land_size: Number(form.land_size) || 15,
      district: form.district,
      location_text: form.location_text,
      main_road: form.main_road,
      electricity: form.electricity,
      clear_deed: form.clear_deed,
      water: form.water,
      bank_loan: form.bank_loan,
      near_town: form.near_town,
      distance_to_town_m: Number(form.distance_to_town_m) || 400,
      period: form.period,
    };
    onSubmit(`[RUN_ESTIMATE] | land | ${JSON.stringify(payload)}`);
  };

  return (
    <div className="bubble">
      <div className="form-step-header">
        <div className="form-step-title">
          <i className="fa-solid fa-mountain-sun" style={{ marginRight: '6px' }}></i> Land Valuation Form
        </div>
        <div className="form-step-dots">
          <div className={`form-dot ${step === 1 ? 'active' : 'completed'}`}></div>
          <div className={`form-dot ${step === 2 ? 'active' : ''}`}></div>
        </div>
      </div>
      <p style={{ fontSize: '12px', color: 'var(--text-gray)', margin: '4px 0 10px 0' }}>
        Step {step} of 2: {step === 1 ? 'Plot Size & Location' : 'Utilities & Facilities'}
      </p>
      <hr className="chat-divider" />

      {/* Step 1 */}
      <div className={`form-step form-step-1 ${step === 1 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div className="input-group">
              <label>Land Size (Perches)</label>
              <input type="number" className="input-field" value={form.land_size} onChange={e => setForm({...form, land_size: e.target.value})} disabled={isSubmitted} placeholder="e.g. 15" />
            </div>
            <div className="input-group">
              <label>District</label>
              <select className="input-field" value={form.district} onChange={e => setForm({...form, district: e.target.value})} disabled={isSubmitted}>
                <option value="Colombo">Colombo</option>
                <option value="Gampaha">Gampaha</option>
                <option value="Kandy">Kandy</option>
                <option value="Galle">Galle</option>
              </select>
            </div>
            <div className="input-group">
              <label>Town / Landmarks</label>
              <input type="text" className="input-field" value={form.location_text} onChange={e => setForm({...form, location_text: e.target.value})} disabled={isSubmitted} placeholder="e.g. Maharagama" />
            </div>
            <div className="input-group">
              <label>Distance to Nearest Town (meters)</label>
              <input type="number" className="input-field" value={form.distance_to_town_m} onChange={e => setForm({...form, distance_to_town_m: e.target.value})} disabled={isSubmitted} placeholder="e.g. 500" />
            </div>
            <button className="cta-btn" onClick={() => setStep(2)} disabled={isSubmitted}>Next: Utilities &nbsp;<i className="fa-solid fa-arrow-right"></i></button>
          </div>
        </div>
      </div>

      {/* Step 2 */}
      <div className={`form-step form-step-2 ${step === 2 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div className="input-group">
              <label>Utilities & Approvals</label>
              <div className="checkbox-grid">
                <label className="checkbox-item"><input type="checkbox" checked={form.main_road} onChange={e => setForm({...form, main_road: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Main road</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.electricity} onChange={e => setForm({...form, electricity: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Electricity</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.clear_deed} onChange={e => setForm({...form, clear_deed: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Clear deed</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.water} onChange={e => setForm({...form, water: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Water</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.bank_loan} onChange={e => setForm({...form, bank_loan: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Bank loan</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.near_town} onChange={e => setForm({...form, near_town: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Near town</label>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn-outline" onClick={() => setStep(1)} style={{ flex: 1 }} disabled={isSubmitted}>Back</button>
              <button className="cta-btn" onClick={handleSubmit} style={{ flex: 2 }} disabled={isSubmitted}>
                {isSubmitted ? <><i className="fa-solid fa-check"></i> Estimated</> : <><i className="fa-solid fa-calculator"></i> Estimate Land Price</>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- 3. RENTAL PREDICTION FORM CARD (2 Steps) ---
const RentalPredictionFormCard: React.FC<{ data: ExtraData; onSubmit: (prompt: string) => void }> = ({ data, onSubmit }) => {
  const [step, setStep] = useState(1);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const ex = data.extracted || {};

  const [form, setForm] = useState({
    property_type: ex.property_type || 'Apartment',
    location: ex.location || 'Colombo 5',
    district: ex.district || 'Colombo',
    furnishing_status: ex.furnishing_status || 'furnished',
    bedrooms: ex.bedrooms || '2',
    bathrooms: ex.bathrooms || '2',
    floor_area_sqft: '1200',
    car_parking_spaces: '1',
    is_short_term: false,
    air_conditioning: true,
    swimming_pool: false,
    gym: false,
    security_24_7: true,
    backup_generator: true,
  });

  const handleSubmit = () => {
    setIsSubmitted(true);
    const payload = {
      property_type: form.property_type,
      location: form.location,
      district: form.district,
      furnishing_status: form.furnishing_status,
      bedrooms: Number(form.bedrooms) || 2,
      bathrooms: Number(form.bathrooms) || 2,
      floor_area_sqft: Number(form.floor_area_sqft) || 1200,
      car_parking_spaces: Number(form.car_parking_spaces) || 1,
      is_short_term: form.is_short_term,
      air_conditioning: form.air_conditioning,
      swimming_pool: form.swimming_pool,
      gym: form.gym,
      security_24_7: form.security_24_7,
      backup_generator: form.backup_generator,
    };
    onSubmit(`[RUN_ESTIMATE] | rental | ${JSON.stringify(payload)}`);
  };

  return (
    <div className="bubble">
      <div className="form-step-header">
        <div className="form-step-title">
          <i className="fa-solid fa-key" style={{ marginRight: '6px' }}></i> Rental Valuation Form
        </div>
        <div className="form-step-dots">
          <div className={`form-dot ${step === 1 ? 'active' : 'completed'}`}></div>
          <div className={`form-dot ${step === 2 ? 'active' : ''}`}></div>
        </div>
      </div>
      <p style={{ fontSize: '12px', color: 'var(--text-gray)', margin: '4px 0 10px 0' }}>
        Step {step} of 2: {step === 1 ? 'Property Type & Location' : 'Furnishing & Amenities'}
      </p>
      <hr className="chat-divider" />

      {/* Step 1 */}
      <div className={`form-step form-step-1 ${step === 1 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div className="input-group">
              <label>Property Type</label>
              <select className="input-field" value={form.property_type} onChange={e => setForm({...form, property_type: e.target.value})} disabled={isSubmitted}>
                <option value="Apartment">Apartment</option>
                <option value="House">House</option>
                <option value="Office space">Office Space</option>
                <option value="Annex">Annex</option>
                <option value="Room">Room</option>
                <option value="Villa">Villa</option>
              </select>
            </div>
            <div className="input-group">
              <label>Location / Area</label>
              <select className="input-field" value={form.location} onChange={e => setForm({...form, location: e.target.value})} disabled={isSubmitted}>
                <option value="Colombo 5">Colombo 5 (Havelock / Thimbirigasyaya)</option>
                <option value="Colombo 3">Colombo 3 (Kollupitiya)</option>
                <option value="Colombo 2">Colombo 2 (Union Place)</option>
                <option value="Dehiwala">Dehiwala</option>
                <option value="Nugegoda">Nugegoda</option>
                <option value="Rajagiriya">Rajagiriya</option>
                <option value="Battaramulla">Battaramulla</option>
              </select>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="input-group">
                <label>Bedrooms</label>
                <input type="number" className="input-field" value={form.bedrooms} onChange={e => setForm({...form, bedrooms: e.target.value})} disabled={isSubmitted} min="1" max="10" />
              </div>
              <div className="input-group">
                <label>Bathrooms</label>
                <input type="number" className="input-field" value={form.bathrooms} onChange={e => setForm({...form, bathrooms: e.target.value})} disabled={isSubmitted} min="1" max="10" />
              </div>
            </div>
            <button className="cta-btn" onClick={() => setStep(2)} disabled={isSubmitted}>Next: Amenities &nbsp;<i className="fa-solid fa-arrow-right"></i></button>
          </div>
        </div>
      </div>

      {/* Step 2 */}
      <div className={`form-step form-step-2 ${step === 2 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div className="input-group">
              <label>Furnishing Status</label>
              <select className="input-field" value={form.furnishing_status} onChange={e => setForm({...form, furnishing_status: e.target.value})} disabled={isSubmitted}>
                <option value="furnished">Furnished</option>
                <option value="semi-furnished">Semi-Furnished</option>
                <option value="unfurnished">Unfurnished</option>
              </select>
            </div>
            <div className="input-group">
              <label>Included Amenities</label>
              <div className="checkbox-grid">
                <label className="checkbox-item"><input type="checkbox" checked={form.air_conditioning} onChange={e => setForm({...form, air_conditioning: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> A/C</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.swimming_pool} onChange={e => setForm({...form, swimming_pool: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Swimming Pool</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.gym} onChange={e => setForm({...form, gym: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Gym</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.security_24_7} onChange={e => setForm({...form, security_24_7: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> 24/7 Security</label>
                <label className="checkbox-item"><input type="checkbox" checked={form.backup_generator} onChange={e => setForm({...form, backup_generator: e.target.checked})} disabled={isSubmitted} /><span className="checkmark"></span> Generator</label>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn-outline" onClick={() => setStep(1)} style={{ flex: 1 }} disabled={isSubmitted}>Back</button>
              <button className="cta-btn" onClick={handleSubmit} style={{ flex: 2 }} disabled={isSubmitted}>
                {isSubmitted ? <><i className="fa-solid fa-check"></i> Estimated</> : <><i className="fa-solid fa-calculator"></i> Estimate Rental</>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- 4. FULL ANALYSIS CARD (Results + LSTM 5-Quarter SVG + RL Recommendation) ---
const FullAnalysisCard: React.FC<{
  data: ExtraData;
  onAskFollowup: (q: string) => void;
}> = ({ data, onAskFollowup }) => {
  const modelType = data.model_type || 'house';
  const price = data.price || 'LKR 0';
  const range = data.range || '';
  const confidence = (data.confidence || 'medium').toLowerCase();
  const rlRec = (data.rl_recommendation || 'HOLD').toUpperCase();
  const sequence = Array.isArray(data.lstm_sequence) && data.lstm_sequence.length > 0 ? data.lstm_sequence : [];
  const labels = data.lstm_labels && data.lstm_labels.length === sequence.length ? data.lstm_labels : ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'];

  // SVG Chart Computations
  const chartWidth = 320;
  const chartHeight = 110;
  const padding = { left: 24, right: 24, top: 16, bottom: 24 };

  const minVal = sequence.length ? Math.min(...sequence) : 0;
  const maxVal = sequence.length ? Math.max(...sequence) : 1;
  const rangeVal = maxVal - minVal || 1;

  const points = sequence.map((v, i) => {
    const x = padding.left + (i * (chartWidth - padding.left - padding.right)) / Math.max(sequence.length - 1, 1);
    const y = padding.top + (1 - (v - minVal) / rangeVal) * (chartHeight - padding.top - padding.bottom);
    return { x, y, value: v };
  });

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaPath = points.length
    ? `${linePath} L ${points[points.length - 1].x} ${chartHeight - padding.bottom} L ${points[0].x} ${chartHeight - padding.bottom} Z`
    : '';

  const formatSeqVal = (val: number) => {
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(0)}k`;
    return Math.round(val).toString();
  };

  const getModelTitle = () => {
    if (modelType === 'house') return { icon: 'fa-house', name: 'Housing Valuation' };
    if (modelType === 'land') return { icon: 'fa-mountain-sun', name: 'Land Valuation' };
    return { icon: 'fa-key', name: 'Rental Valuation' };
  };

  const modelInfo = getModelTitle();

  return (
    <div className="analysis-card">
      <div className="analysis-header-row">
        <div className="analysis-model-tag">
          <i className={`fa-solid ${modelInfo.icon}`} style={{ color: 'var(--blue-medium)' }}></i>
          <span>{modelInfo.name}</span>
        </div>
        <div className={`analysis-conf-badge ${confidence}`}>
          {confidence} confidence
        </div>
      </div>

      <div className="analysis-price-box">
        <span className="analysis-price-label">Predicted Market Valuation</span>
        <div className="analysis-price-value">{price}</div>
        {range && (
          <div className="analysis-range-tag">
            <i className="fa-solid fa-circle-check"></i> Range: {range}
          </div>
        )}
        {data.total_value && (
          <div style={{ fontSize: '13px', color: 'var(--text-gray)', marginTop: '2px' }}>
            Whole Plot Value: <strong>{data.total_value}</strong>
          </div>
        )}
      </div>

      {/* RL Recommendation Box */}
      <div className="analysis-rl-container">
        <div>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-gray)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            RL Agent Recommendation
          </div>
          <div style={{ fontSize: '12px', color: 'var(--primary-dark)', marginTop: '2px' }}>
            Based on multi-source market signals
          </div>
        </div>
        <div className={`rl-pill ${rlRec.includes('BUY') ? 'buy' : rlRec.includes('SELL') ? 'sell' : 'hold'}`}>
          <i className={`fa-solid ${rlRec.includes('BUY') ? 'fa-arrow-trend-up' : rlRec.includes('SELL') ? 'fa-arrow-trend-down' : 'fa-hand'}`}></i>
          {rlRec}
        </div>
      </div>

      {/* In-Chat LSTM 5-Quarter SVG Forecast */}
      {sequence.length > 0 && (
        <div className="analysis-lstm-section">
          <div className="analysis-section-title">
            <i className="fa-solid fa-chart-line" style={{ color: 'var(--blue-medium)' }}></i>
            LSTM 5-Quarter Price Trajectory
          </div>
          <div className="chat-svg-container">
            <svg className="chat-forecast-svg" viewBox={`0 0 ${chartWidth} ${chartHeight}`}>
              <defs>
                <linearGradient id="chatForecastGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4445ff" stopOpacity="0.35" />
                  <stop offset="100%" stopColor="#4445ff" stopOpacity="0.02" />
                </linearGradient>
              </defs>
              <path d={areaPath} fill="url(#chatForecastGrad)" />
              <path d={linePath} fill="none" stroke="#4445ff" strokeWidth="2.5" strokeLinecap="round" />
              {points.map((p, i) => (
                <g key={i}>
                  <circle cx={p.x} cy={p.y} r="3.5" fill="#4445ff" stroke="#ffffff" strokeWidth="1.5" />
                  <text x={p.x} y={p.y - 7} textAnchor="middle" fontSize="9" fontWeight="bold" fill="var(--primary-dark)">
                    {formatSeqVal(p.value)}
                  </text>
                  <text x={p.x} y={chartHeight - 6} textAnchor="middle" fontSize="9" fill="var(--text-gray)">
                    {labels[i] || `Q${i+1}`}
                  </text>
                </g>
              ))}
            </svg>
          </div>
        </div>
      )}

      {/* Reasoning Box */}
      {data.reasoning && (
        <div className="analysis-reasoning-box">
          <strong>Market Context: </strong>
          {data.reasoning}
        </div>
      )}

      {/* Quick Interactive Actions */}
      <div className="analysis-actions-row">
        <button className="analysis-action-btn" onClick={() => onAskFollowup(`Why did the RL model suggest ${rlRec} for this ${modelType}?`)}>
          <i className="fa-regular fa-comment-dots"></i> Why {rlRec}?
        </button>
        <button className="analysis-action-btn" onClick={() => onAskFollowup(`How does the price trend look for ${data.location || 'this property'} over the next 2 years?`)}>
          <i className="fa-solid fa-arrow-trend-up"></i> Long-term outlook
        </button>
        <Link to={modelType === 'house' ? '/house-price' : modelType === 'land' ? '/land-price' : '/rental-price'} className="analysis-action-btn" style={{ textDecoration: 'none' }}>
          <i className="fa-solid fa-map-location-dot"></i> Market Explorer
        </Link>
      </div>
    </div>
  );
};

const PriceGraph: React.FC = () => (
  <div className="bubble">
    <p>Here is the price trend visualization across Sri Lankan real estate over recent periods:</p>
    <div className="chat-chart-container">
      <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '10px', fontFamily: 'fontExtraBold' }}>Real Estate Index Trend (LKR)</div>
      <div className="bar-chart">
        <div className="bar-group"><span className="bar-value">1.1M</span><div className="bar" style={{ height: '35%' }}></div><span className="bar-label">2023<br/>H1</span></div>
        <div className="bar-group"><span className="bar-value">1.3M</span><div className="bar" style={{ height: '48%' }}></div><span className="bar-label">2023<br/>H2</span></div>
        <div className="bar-group"><span className="bar-value">1.45M</span><div className="bar" style={{ height: '55%' }}></div><span className="bar-label">2024<br/>H1</span></div>
        <div className="bar-group"><span className="bar-value">1.6M</span><div className="bar" style={{ height: '62%' }}></div><span className="bar-label">2024<br/>H2</span></div>
        <div className="bar-group"><span className="bar-value">1.8M</span><div className="bar" style={{ height: '72%' }}></div><span className="bar-label">2025<br/>H1</span></div>
        <div className="bar-group"><span className="bar-value">2.1M</span><div className="bar" style={{ height: '84%' }}></div><span className="bar-label">2025<br/>H2</span></div>
        <div className="bar-group"><span className="bar-value">2.45M</span><div className="bar highlight" style={{ height: '95%' }}></div><span className="bar-label">2026<br/>H1</span></div>
        <div className="bar-group"><span className="bar-value">2.5M</span><div className="bar" style={{ height: '98%', opacity: 0.5, border: '1.5px dashed var(--blue-medium)', boxSizing: 'border-box' }}></div><span className="bar-label">Pred.<br/>&nbsp;</span></div>
      </div>
    </div>
  </div>
);

// --- 5. ADD HOUSING FORM CARD (2 Steps, Teal Accent) ---
const AddHousingFormCard: React.FC<{ data: ExtraData; onSubmit: (prompt: string) => void }> = ({ data, onSubmit }) => {
  const ext = data.extracted || {};
  const [step, setStep] = useState(1);
  const [location, setLocation] = useState(ext.location || 'Moratuwa');
  const [purchasePrice, setPurchasePrice] = useState(ext.purchase_price || '25000000');
  const [purchaseDate, setPurchaseDate] = useState(ext.purchase_date || new Date().toISOString().split('T')[0]);
  const [landPerches, setLandPerches] = useState(ext.land_size_perches || '10');
  const [houseSqft, setHouseSqft] = useState(ext.house_size_sqft || ext.house_sqft || '1800');
  const [floors, setFloors] = useState(ext.floors || '2');
  const [builtYear, setBuiltYear] = useState(ext.built_year || '2022');
  const [condition, setCondition] = useState(ext.property_condition || 'good');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      location,
      purchase_price: parseFloat(purchasePrice) || 0,
      purchase_date: purchaseDate,
      land_size_perches: parseFloat(landPerches) || 10,
      house_size_sqft: parseFloat(houseSqft) || 1500,
      floors: parseInt(floors) || 1,
      built_year: parseInt(builtYear) || 2023,
      property_condition: condition,
    };
    onSubmit(`[ADD_PROPERTY] | housing | ${JSON.stringify(payload)}`);
  };

  return (
    <div className="analysis-card add-property-card">
      <div className="analysis-header-row">
        <div className="analysis-model-tag">
          <i className="fa-solid fa-house-chimney-medical" style={{ color: '#00b4aa' }}></i>
          <span>Add Housing Asset</span>
        </div>
        <div className="form-step-dots">
          <span className={`form-step-dot ${step === 1 ? 'active' : ''}`} onClick={() => setStep(1)} />
          <span className={`form-step-dot ${step === 2 ? 'active' : ''}`} onClick={() => setStep(2)} />
        </div>
      </div>

      <div className="form-step-header">
        <strong>Step {step} of 2:</strong> {step === 1 ? 'Location & Purchase Info' : 'House Specifications'}
      </div>

      <form onSubmit={handleSubmit} className="analysis-prediction-form">
        {step === 1 && (
          <>
            <div className="form-row">
              <label className="form-label">Property Location</label>
              <input
                type="text"
                className="form-input"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Moratuwa, Colombo"
                required
              />
            </div>
            <div className="form-grid-2">
              <div className="form-row">
                <label className="form-label">Purchase Price (LKR)</label>
                <input
                  type="number"
                  className="form-input"
                  value={purchasePrice}
                  onChange={(e) => setPurchasePrice(e.target.value)}
                  placeholder="e.g. 25000000"
                  required
                />
              </div>
              <div className="form-row">
                <label className="form-label">Purchase Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={purchaseDate}
                  onChange={(e) => setPurchaseDate(e.target.value)}
                  required
                />
              </div>
            </div>
            <button type="button" className="btn-primary form-submit-btn" onClick={() => setStep(2)}>
              Next Step <i className="fa-solid fa-arrow-right" style={{ marginLeft: '6px' }}></i>
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <div className="form-grid-2">
              <div className="form-row">
                <label className="form-label">House Size (sqft)</label>
                <input
                  type="number"
                  className="form-input"
                  value={houseSqft}
                  onChange={(e) => setHouseSqft(e.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label className="form-label">Land Size (Perches)</label>
                <input
                  type="number"
                  className="form-input"
                  value={landPerches}
                  onChange={(e) => setLandPerches(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="form-grid-2">
              <div className="form-row">
                <label className="form-label">Number of Floors</label>
                <input
                  type="number"
                  className="form-input"
                  value={floors}
                  onChange={(e) => setFloors(e.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label className="form-label">Built Year</label>
                <input
                  type="number"
                  className="form-input"
                  value={builtYear}
                  onChange={(e) => setBuiltYear(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="form-row">
              <label className="form-label">Property Condition</label>
              <select
                className="form-select"
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
              >
                <option value="new">Brand New</option>
                <option value="good">Good Condition</option>
                <option value="need renovation">Needs Renovation</option>
              </select>
            </div>
            <div className="form-grid-2">
              <button type="button" className="btn-secondary form-submit-btn" onClick={() => setStep(1)}>
                Back
              </button>
              <button type="submit" className="btn-primary form-submit-btn">
                <i className="fa-solid fa-plus-circle" style={{ marginRight: '6px' }}></i> Save to Portfolio
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
};

// --- 6. ADD RENTAL FORM CARD ---
const AddRentalFormCard: React.FC<{ data: ExtraData; onSubmit: (prompt: string) => void }> = ({ data, onSubmit }) => {
  const ext = data.extracted || {};
  const [step, setStep] = useState(1);
  const [location, setLocation] = useState(ext.location || 'Colombo 5');
  const [purchasePrice, setPurchasePrice] = useState(ext.purchase_price || '35000000');
  const [purchaseDate, setPurchaseDate] = useState(ext.purchase_date || new Date().toISOString().split('T')[0]);
  const [monthlyRent, setMonthlyRent] = useState(ext.monthly_rent || '150000');
  const [occupancy, setOccupancy] = useState(ext.occupancy_status || 'occupied');
  const [leaseStart, setLeaseStart] = useState(ext.lease_start_date || new Date().toISOString().split('T')[0]);
  const [leaseEnd, setLeaseEnd] = useState(ext.lease_end_date || new Date(Date.now() + 365*24*3600*1000).toISOString().split('T')[0]);
  const [tenantType, setTenantType] = useState(ext.tenant_type || 'family');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      location,
      purchase_price: parseFloat(purchasePrice) || 0,
      purchase_date: purchaseDate,
      monthly_rent: parseFloat(monthlyRent) || 0,
      occupancy_status: occupancy,
      lease_start_date: leaseStart,
      lease_end_date: leaseEnd,
      tenant_type: tenantType,
    };
    onSubmit(`[ADD_PROPERTY] | rental | ${JSON.stringify(payload)}`);
  };

  return (
    <div className="analysis-card add-property-card">
      <div className="analysis-header-row">
        <div className="analysis-model-tag">
          <i className="fa-solid fa-building-circle-check" style={{ color: '#00b4aa' }}></i>
          <span>Add Rental Asset</span>
        </div>
        <div className="form-step-dots">
          <span className={`form-step-dot ${step === 1 ? 'active' : ''}`} onClick={() => setStep(1)} />
          <span className={`form-step-dot ${step === 2 ? 'active' : ''}`} onClick={() => setStep(2)} />
        </div>
      </div>

      <div className="form-step-header">
        <strong>Step {step} of 2:</strong> {step === 1 ? 'Asset Location & Cost' : 'Rental & Tenant Info'}
      </div>

      <form onSubmit={handleSubmit} className="analysis-prediction-form">
        {step === 1 && (
          <>
            <div className="form-row">
              <label className="form-label">Location / Address</label>
              <input
                type="text"
                className="form-input"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Colombo 5"
                required
              />
            </div>
            <div className="form-grid-2">
              <div className="form-row">
                <label className="form-label">Purchase Price (LKR)</label>
                <input
                  type="number"
                  className="form-input"
                  value={purchasePrice}
                  onChange={(e) => setPurchasePrice(e.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label className="form-label">Purchase Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={purchaseDate}
                  onChange={(e) => setPurchaseDate(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="form-row">
              <label className="form-label">Monthly Rent (LKR)</label>
              <input
                type="number"
                className="form-input"
                value={monthlyRent}
                onChange={(e) => setMonthlyRent(e.target.value)}
                required
              />
            </div>
            <button type="button" className="btn-primary form-submit-btn" onClick={() => setStep(2)}>
              Next Step <i className="fa-solid fa-arrow-right" style={{ marginLeft: '6px' }}></i>
            </button>

          </>
        )}

        {step === 2 && (
          <>
            <div className="form-grid-2">
              <div className="form-row">
                <label className="form-label">Occupancy Status</label>
                <select className="form-select" value={occupancy} onChange={(e) => setOccupancy(e.target.value)}>
                  <option value="occupied">Occupied</option>
                  <option value="vacant">Vacant</option>
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">Tenant Type</label>
                <select className="form-select" value={tenantType} onChange={(e) => setTenantType(e.target.value)}>
                  <option value="family">Family</option>
                  <option value="office">Office / Corporate</option>
                  <option value="commercial">Commercial</option>
                </select>
              </div>
            </div>
            <div className="form-grid-2">
              <div className="form-row">
                <label className="form-label">Lease Start</label>
                <input type="date" className="form-input" value={leaseStart} onChange={(e) => setLeaseStart(e.target.value)} />
              </div>
              <div className="form-row">
                <label className="form-label">Lease End</label>
                <input type="date" className="form-input" value={leaseEnd} onChange={(e) => setLeaseEnd(e.target.value)} />
              </div>
            </div>
            <div className="form-grid-2">
              <button type="button" className="btn-secondary form-submit-btn" onClick={() => setStep(1)}>
                Back
              </button>
              <button type="submit" className="btn-primary form-submit-btn">
                <i className="fa-solid fa-plus-circle" style={{ marginRight: '6px' }}></i> Save to Portfolio
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
};

// --- 7. ADD LAND FORM CARD ---
const AddLandFormCard: React.FC<{ data: ExtraData; onSubmit: (prompt: string) => void }> = ({ data, onSubmit }) => {
  const ext = data.extracted || {};
  const [step, setStep] = useState(1);
  const [location, setLocation] = useState(ext.location || 'Maharagama');
  const [purchasePrice, setPurchasePrice] = useState(ext.purchase_price || '18000000');
  const [purchaseDate, setPurchaseDate] = useState(ext.purchase_date || new Date().toISOString().split('T')[0]);
  const [landSize, setLandSize] = useState(ext.land_size || '12');
  const [zoning, setZoning] = useState(ext.zoning_type || 'residential');
  const [roadAccess, setRoadAccess] = useState(ext.road_access || '20ft Carpet Road');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      location,
      purchase_price: parseFloat(purchasePrice) || 0,
      purchase_date: purchaseDate,
      land_size: parseFloat(landSize) || 10,
      zoning_type: zoning,
      road_access: roadAccess,
    };
    onSubmit(`[ADD_PROPERTY] | land | ${JSON.stringify(payload)}`);
  };

  return (
    <div className="analysis-card add-property-card">
      <div className="analysis-header-row">
        <div className="analysis-model-tag">
          <i className="fa-solid fa-tree-city" style={{ color: '#00b4aa' }}></i>
          <span>Add Land Plot</span>
        </div>
        <div className="form-step-dots">
          <span className={`form-step-dot ${step === 1 ? 'active' : ''}`} onClick={() => setStep(1)} />
          <span className={`form-step-dot ${step === 2 ? 'active' : ''}`} onClick={() => setStep(2)} />
        </div>
      </div>

      <div className="form-step-header">
        <strong>Step {step} of 2:</strong> {step === 1 ? 'Location & Price' : 'Plot Specifications'}
      </div>

      <form onSubmit={handleSubmit} className="analysis-prediction-form">
        {step === 1 && (
          <>
            <div className="form-row">
              <label className="form-label">Plot Location</label>
              <input
                type="text"
                className="form-input"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Maharagama"
                required
              />
            </div>
            <div className="form-grid-2">
              <div className="form-row">
                <label className="form-label">Purchase Price (LKR)</label>
                <input
                  type="number"
                  className="form-input"
                  value={purchasePrice}
                  onChange={(e) => setPurchasePrice(e.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label className="form-label">Purchase Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={purchaseDate}
                  onChange={(e) => setPurchaseDate(e.target.value)}
                  required
                />
              </div>
            </div>
            <button type="button" className="btn-primary form-submit-btn" onClick={() => setStep(2)}>
              Next Step <i className="fa-solid fa-arrow-right" style={{ marginLeft: '6px' }}></i>
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <div className="form-grid-2">
              <div className="form-row">
                <label className="form-label">Plot Size (Perches)</label>
                <input
                  type="number"
                  className="form-input"
                  value={landSize}
                  onChange={(e) => setLandSize(e.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label className="form-label">Zoning Type</label>
                <select className="form-select" value={zoning} onChange={(e) => setZoning(e.target.value)}>
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                  <option value="agricultural">Agricultural</option>
                </select>
              </div>
            </div>
            <div className="form-row">
              <label className="form-label">Road Access</label>
              <input
                type="text"
                className="form-input"
                value={roadAccess}
                onChange={(e) => setRoadAccess(e.target.value)}
                placeholder="e.g. 20ft Carpeted Road"
                required
              />
            </div>
            <div className="form-grid-2">
              <button type="button" className="btn-secondary form-submit-btn" onClick={() => setStep(1)}>
                Back
              </button>
              <button type="submit" className="btn-primary form-submit-btn">
                <i className="fa-solid fa-plus-circle" style={{ marginRight: '6px' }}></i> Save to Portfolio
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
};

// --- 8. PORTFOLIO SUMMARY CARD ---
const PortfolioSummaryCard: React.FC<{
  summary: ExtraData['summary'];
  properties?: ExtraData['properties'];
  onAction: (query: string) => void;
}> = ({ summary, properties = [], onAction }) => {
  if (!summary) return null;

  const formatLKR = (val: number) => {
    if (!val) return 'LKR 0';
    if (val >= 1_000_000) return `LKR ${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 100_000) return `LKR ${(val / 100_000).toFixed(1)}L`;
    return `LKR ${val.toLocaleString()}`;
  };

  const mix = summary.property_mix || { housing: 0, rental: 0, land: 0 };
  const isPositive = summary.total_profit >= 0;

  return (
    <div className="portfolio-summary-card">
      <div className="portfolio-summary-header">
        <div className="portfolio-summary-title">
          <i className="fa-solid fa-wallet" style={{ color: 'var(--blue-medium)' }}></i>
          <span>Real Estate Portfolio</span>
        </div>
        <div className={`rl-pill ${summary.sentiment === 'good' || summary.sentiment === 'high' ? 'buy' : 'hold'}`} style={{ fontSize: '11px', padding: '4px 10px' }}>
          <i className="fa-solid fa-chart-line"></i> {summary.sentiment?.toUpperCase() || 'GOOD'}
        </div>
      </div>

      <div className="portfolio-hero-box">
        <span className="portfolio-hero-label">Total Portfolio Valuation</span>
        <div className="portfolio-hero-value">{formatLKR(summary.portfolio_value)}</div>
      </div>

      <div className="portfolio-metrics-row">
        <div className="portfolio-metric-chip">
          <span className="portfolio-metric-label">Unrealized Gain</span>
          <span className="portfolio-metric-val" style={{ color: isPositive ? '#15803d' : '#b91c1c' }}>
            {isPositive ? '+' : ''}{formatLKR(summary.total_profit)} ({summary.growth_percentage}%)
          </span>
        </div>
        <div className="portfolio-metric-chip">
          <span className="portfolio-metric-label">Total Capital Invested</span>
          <span className="portfolio-metric-val">{formatLKR(summary.total_investment)}</span>
        </div>
      </div>

      <div className="portfolio-mix-strip">
        <div className="portfolio-mix-item">
          <i className="fa-solid fa-house"></i>
          <span><strong>{mix.housing}</strong> Housing</span>
        </div>
        <div className="portfolio-mix-item">
          <i className="fa-solid fa-building"></i>
          <span><strong>{mix.rental}</strong> Rentals</span>
        </div>
        <div className="portfolio-mix-item">
          <i className="fa-solid fa-tree"></i>
          <span><strong>{mix.land}</strong> Lands</span>
        </div>
      </div>

      {properties.length > 0 && (
        <PropertyListCard properties={properties} onAction={onAction} />
      )}

      <div className="analysis-actions-row">
        <button className="analysis-action-btn" onClick={() => onAction('How can I optimize the returns on my portfolio?')}>
          <i className="fa-solid fa-brain"></i> AI Portfolio Advice
        </button>
        <button className="analysis-action-btn" onClick={() => onAction('I want to add a property to my portfolio')}>
          <i className="fa-solid fa-plus"></i> Add Property
        </button>
        <Link to="/dashboard" className="analysis-action-btn" style={{ textDecoration: 'none' }}>
          <i className="fa-solid fa-table-columns"></i> Full Dashboard
        </Link>
      </div>
    </div>
  );
};

// --- 9. PROPERTY LIST CARD ---
const PropertyListCard: React.FC<{
  properties: NonNullable<ExtraData['properties']>;
  onAction: (query: string) => void;
}> = ({ properties, onAction }) => {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const formatLKR = (val: number) => {
    if (!val) return '-';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 100_000) return `${(val / 100_000).toFixed(1)}L`;
    return val.toLocaleString();
  };

  return (
    <div className="property-list-card">
      <div className="property-list-header">
        <div className="property-list-title">
          <i className="fa-solid fa-list-check" style={{ color: 'var(--blue-medium)' }}></i>
          <span>Tracked Properties</span>
        </div>
        <span className="property-list-count">{properties.length} Assets</span>
      </div>

      <div className="property-list-items">
        {properties.map((p) => {
          const isExpanded = expandedId === p.property_id;
          const isPositive = p.profit >= 0;
          const icon = p.type === 'housing' ? 'fa-house' : p.type === 'rental' ? 'fa-building' : 'fa-tree';

          return (
            <div
              key={p.property_id}
              className="property-item-card"
              onClick={() => setExpandedId(isExpanded ? null : p.property_id)}
            >
              <div className="property-item-header">
                <div className="property-item-main">
                  <div className="property-item-icon">
                    <i className={`fa-solid ${icon}`}></i>
                  </div>
                  <div>
                    <div className="property-item-loc">{p.location}</div>
                    <div className="property-item-type">{p.type}</div>
                  </div>
                </div>
                <div className={`rl-pill ${p.sentiment.includes('high') || p.sentiment.includes('good') ? 'buy' : 'hold'}`} style={{ fontSize: '10px', padding: '3px 8px' }}>
                  {p.sentiment}
                </div>
              </div>

              <div className="property-item-grid">
                <div className="property-item-col">
                  <span className="property-item-col-label">Bought</span>
                  <span className="property-item-col-val">{formatLKR(p.purchase_price)}</span>
                </div>
                <div className="property-item-col">
                  <span className="property-item-col-label">Current</span>
                  <span className="property-item-col-val" style={{ color: 'var(--blue-medium)' }}>{formatLKR(p.current_value)}</span>
                </div>
                <div className="property-item-col">
                  <span className="property-item-col-label">Profit</span>
                  <span className={`property-item-col-val ${isPositive ? 'positive' : 'negative'}`}>
                    {isPositive ? '+' : ''}{formatLKR(p.profit)}
                  </span>
                </div>
              </div>

              {isExpanded && (
                <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-light)', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                  <button
                    className="analysis-action-btn"
                    style={{ fontSize: '11px', padding: '4px 8px' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onAction(`Predict the updated market price and LSTM trend for my ${p.type} in ${p.location}`);
                    }}
                  >
                    <i className="fa-solid fa-calculator"></i> Run Valuation
                  </button>
                  <button
                    className="analysis-action-btn"
                    style={{ fontSize: '11px', padding: '4px 8px' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      onAction(`Should I hold or sell my ${p.type} in ${p.location}?`);
                    }}
                  >
                    <i className="fa-solid fa-hand-holding-dollar"></i> RL Signal
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// --- 10. ADD PROPERTY SUCCESS CARD ---
const AddPropertySuccessCard: React.FC<{
  data: ExtraData;
  onAction: (query: string) => void;
}> = ({ data, onAction }) => (
  <div className="add-prop-success-card">
    <div className="add-prop-success-title">
      <i className="fa-solid fa-circle-check"></i>
      <span>Property Added to Portfolio!</span>
    </div>
    <p style={{ fontSize: '13px', color: 'var(--primary-dark)', margin: 0 }}>
      {data.location ? (
        <>Your <strong>{data.property_type || 'property'}</strong> in <strong>{data.location}</strong> ({data.purchase_price}) is now active in your real estate portfolio.</>
      ) : (
        <>Your property was saved successfully to your portfolio and indexed in memory.</>
      )}
    </p>
    <div className="analysis-actions-row">
      <button className="analysis-action-btn" onClick={() => onAction('Show my portfolio overview and tracked assets')}>
        <i className="fa-solid fa-wallet"></i> View Portfolio
      </button>
      <button className="analysis-action-btn" onClick={() => onAction(`Predict the future price forecast for this property in ${data.location || 'my portfolio'}`)}>
        <i className="fa-solid fa-chart-line"></i> Predict Future Forecast
      </button>
    </div>
  </div>
);


interface ChatSessionItem {
  id: string;
  title: string;
  updated_at?: string;
}


// --- Main Page Component ---

const Askreva: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { openAuthModal } = useAuth();
  const from = location.state?.from || '/';

  const [userName, setUserName] = useState<string>('User');
  const [userProfileUrl, setUserProfileUrl] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<ChatSessionItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(false);

  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const baseTranscriptRef = useRef('');
  const finalTranscriptRef = useRef('');
  const latestTranscriptRef = useRef('');
  const speechStartTimerRef = useRef<number | null>(null);
  const holdTimerRef = useRef<number | null>(null);
  const holdModeRef = useRef(false);
  const suppressClickRef = useRef(false);
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState('');

  const fetchSessions = async () => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (!token) return;

    try {
      setIsLoadingSessions(true);
      const res = await fetch(`${API_BASE_URL}/chat/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
    } catch (err) {
      console.error('Error fetching chat sessions:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const loadSession = async (sessionId: string) => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (!token) return;

    try {
      setIsTyping(true);
      const res = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setActiveSessionId(sessionId);
        setMessages(data.messages || []);
        setIsSidebarOpen(false);
      }
    } catch (err) {
      console.error('Error loading session:', err);
    } finally {
      setIsTyping(false);
    }
  };

  const startNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setIsSidebarOpen(false);
  };

  const deleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (activeSessionId === sessionId) {
          startNewChat();
        }
      }
    } catch (err) {
      console.error('Error deleting session:', err);
    }
  };

  // Authentication check (same as Dashboard)
  useEffect(() => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const email = localStorage.getItem('user_email') || sessionStorage.getItem('user_email');
    const displayName = localStorage.getItem('user_name') || sessionStorage.getItem('user_name');
    const storedPicture = localStorage.getItem('user_picture') || sessionStorage.getItem('user_picture');

    if (!token || !email) {
      navigate('/', { replace: true });
      openAuthModal('login', '/askreva');
      return;
    }

    setUserName(
      displayName || (email ? email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1) : 'User')
    );
    setUserProfileUrl(storedPicture || null);

    fetchSessions();
  }, [navigate, openAuthModal]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    return () => {
      if (speechStartTimerRef.current) {
        window.clearTimeout(speechStartTimerRef.current);
      }
      if (holdTimerRef.current) {
        window.clearTimeout(holdTimerRef.current);
      }
      recognitionRef.current?.abort();
    };
  }, []);

  const cleanSpeechTranscript = (text: string) => {
    let cleaned = text
      .replace(/\s+/g, ' ')
      .replace(/\s+([,.!?])/g, '$1')
      .trim();

    const corrections: Array<[RegExp, string]> = [
      [/\b(reba|riva|river|rev a|reva)\b/gi, 'Reva'],
      [/\bmore to work\b/gi, 'Moratuwa'],
      [/\bmora two a\b/gi, 'Moratuwa'],
      [/\bmore two a\b/gi, 'Moratuwa'],
      [/\bcolumbo\b/gi, 'Colombo'],
      [/\bgampa ha\b/gi, 'Gampaha'],
      [/\bkaluthara\b/gi, 'Kalutara'],
      [/\bperches\b/gi, 'perches'],
      [/\bperch\b/gi, 'perch']
    ];

    corrections.forEach(([wrong, right]) => {
      cleaned = cleaned.replace(wrong, right);
    });

    return cleaned;
  };

  const getSpeechErrorMessage = (error: string) => {
    if (error === 'network') {
      return 'Voice recognition failed because of a network issue. Please check your connection and try again.';
    }
    if (error === 'not-allowed' || error === 'service-not-allowed') {
      return 'Microphone access is blocked. Please allow microphone permission in your browser.';
    }
    if (error === 'no-speech') {
      return 'No speech was detected. Please speak clearly after the mic starts listening.';
    }
    if (error === 'audio-capture') {
      return 'No microphone was found. Please check your microphone connection.';
    }
    if (error === 'aborted') {
      return '';
    }
    return 'Speech recognition failed. Please try again.';
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const newUserMsg: Message = { id: Date.now().toString(), text, sender: 'user', type: 'text' };
    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    setIsTyping(true);

    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: text,
          session_id: activeSessionId
        })
      });
      const data = await response.json();
      
      if (data.session_id) {
        setActiveSessionId(data.session_id);
        fetchSessions();
      }

      const newBotMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: data.reply || "I'm sorry, I encountered an error processing that.",
        sender: 'reva',
        type: data.type || 'text',
        extraData: data
      };
      setMessages(prev => [...prev, newBotMsg]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          text: "Could not connect to the Reva server. Make sure your FastAPI server is running on port 8000.",
          sender: 'reva',
          type: 'text'
        }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const startSpeechToText = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSpeechError('Speech recognition is not supported in this browser. Please try Google Chrome.');
      return;
    }

    if (recognitionRef.current) {
      return;
    }

    setSpeechError('');
    baseTranscriptRef.current = inputValue.trim();
    finalTranscriptRef.current = '';
    latestTranscriptRef.current = inputValue.trim();

    const recognition = new SpeechRecognition();

    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 3;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript.trim();

        if (event.results[i].isFinal) {
          finalTranscriptRef.current = `${finalTranscriptRef.current} ${transcript}`.trim();
        } else {
          interimTranscript = `${interimTranscript} ${transcript}`.trim();
        }
      }

      const combinedTranscript = `${baseTranscriptRef.current} ${finalTranscriptRef.current} ${interimTranscript}`
        .replace(/\s+/g, ' ')
        .trim();

      latestTranscriptRef.current = cleanSpeechTranscript(combinedTranscript);
      setInputValue(latestTranscriptRef.current);

      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      }
    };

    recognition.onerror = (event: any) => {
      const message = getSpeechErrorMessage(event.error);
      if (message) {
        setSpeechError(message);
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;

      const finalText = cleanSpeechTranscript(latestTranscriptRef.current);
      setInputValue(finalText);

      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      }
    };

    recognitionRef.current = recognition;

    speechStartTimerRef.current = window.setTimeout(() => {
      try {
        recognition.start();
      } catch (error) {
        recognitionRef.current = null;
        setIsListening(false);
        setSpeechError('Could not start voice recognition. Please try again.');
      }
    }, 300);
  };

  const stopSpeechToText = () => {
    if (speechStartTimerRef.current) {
      window.clearTimeout(speechStartTimerRef.current);
      speechStartTimerRef.current = null;
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };

  const toggleSpeechToText = () => {
    if (suppressClickRef.current) {
      suppressClickRef.current = false;
      return;
    }

    if (isListening) {
      stopSpeechToText();
    } else {
      startSpeechToText();
    }
  };

  const handleMicPointerDown = () => {
    holdModeRef.current = false;

    holdTimerRef.current = window.setTimeout(() => {
      holdModeRef.current = true;
      if (!isListening) {
        startSpeechToText();
      }
    }, 250);
  };

  const handleMicPointerUp = () => {
    if (holdTimerRef.current) {
      window.clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }

    if (holdModeRef.current) {
      suppressClickRef.current = true;
      stopSpeechToText();
      holdModeRef.current = false;
    }
  };

  const triggerSuggestion = (text: string) => {
    handleSendMessage(text);
  };

  return (
    <div className="askreva-page" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', backgroundColor: 'var(--primary-bg)', fontFamily: 'fontRegular, sans-serif' }}>
      
      {/* Sidebar Overlays */}
      <div className={`sidebar-overlay ${isSidebarOpen ? 'show' : ''}`} onClick={() => setIsSidebarOpen(false)}></div>
      <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`} id="sidebar">
        <div className="sidebar-header">
          <h3>Previous Chats</h3>
          <i className="fa-solid fa-xmark" onClick={() => setIsSidebarOpen(false)} style={{ cursor: 'pointer' }}></i>
        </div>

        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-light)' }}>
          <button
            onClick={startNewChat}
            style={{
              width: '100%',
              padding: '10px 14px',
              fontSize: '13px',
              fontWeight: 600,
              background: 'var(--blue-medium)',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: 'pointer',
              transition: '0.2s'
            }}
          >
            <i className="fa-solid fa-plus"></i> New Chat
          </button>
        </div>

        <ul className="chat-history" id="historyList">
          {isLoadingSessions ? (
            <li style={{ color: 'var(--text-gray)', fontSize: '13px' }}>Loading history...</li>
          ) : sessions.length === 0 ? (
            <li style={{ color: 'var(--text-gray)', fontSize: '13px' }}>No previous chats</li>
          ) : (
            sessions.map((s) => (
              <li
                key={s.id}
                onClick={() => loadSession(s.id)}
                style={{
                  fontWeight: activeSessionId === s.id ? 700 : 400,
                  background: activeSessionId === s.id ? 'var(--chat-history-hover)' : 'transparent',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                  <i className="fa-regular fa-message" style={{ fontSize: '14px', flexShrink: 0 }}></i>
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.title}
                  </span>
                </div>
                <i
                  className="fa-regular fa-trash-can"
                  onClick={(e) => deleteSession(e, s.id)}
                  style={{ opacity: 0.6, cursor: 'pointer', fontSize: '13px', marginLeft: '8px' }}
                  title="Delete session"
                ></i>
              </li>
            ))
          )}
        </ul>
      </div>

      {/* Header */}
      <header className="chat-header">
        <div className="header-left">
          <img src="/img/icons/bars.svg" className="hamburger-icon" alt="Menu" onClick={() => setIsSidebarOpen(true)} />
        </div>
        <div className="header-center">
          {/* 3. Replaced "/" with dynamic {from} path */}
          <Link to={from} className="back-btn"><i className="fa-solid fa-chevron-left"></i></Link>
          <span className="agent-name">Ask Rēva</span>
          <img src="/img/icons/chat.svg" alt="Chat" className="chat-icon" />
        </div>
        <div className="header-right">
          <img
            src={userProfileUrl || generateInitialsAvatar(userName)}
            className="user-avatar"
            alt={`${userName} Profile`}
            style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }}
          />
        </div>
      </header>

      {/* Chat Container */}
      <div className="chat-container">
        {messages.length === 0 && (
          <div className="initial-state">
            <h2>What can I help with today?</h2>
            <div className="suggestion-grid">
              <div className="suggestion-chip" onClick={() => triggerSuggestion('predict a price of a house near moratuwa with 3 bedrooms and electricity')}>
                <i className="fa-solid fa-house" style={{ color: 'var(--blue-medium)', fontSize: '15px' }}></i>
                House price valuation
              </div>
              <div className="suggestion-chip" onClick={() => triggerSuggestion('I need a rental price prediction for a 2 bedroom apartment in Colombo 5')}>
                <i className="fa-solid fa-key" style={{ color: 'var(--blue-medium)', fontSize: '15px' }}></i>
                Rental price valuation
              </div>
              <div className="suggestion-chip" onClick={() => triggerSuggestion('I need a land price prediction for 15 perches in Maharagama')}>
                <i className="fa-solid fa-mountain-sun" style={{ color: 'var(--blue-medium)', fontSize: '15px' }}></i>
                Land price estimation
              </div>
              <div className="suggestion-chip" onClick={() => triggerSuggestion('Show my real estate portfolio')}>
                <i className="fa-solid fa-wallet" style={{ color: '#00b4aa', fontSize: '15px' }}></i>
                View My Portfolio
              </div>
              <div className="suggestion-chip" onClick={() => triggerSuggestion('I want to add a property to my portfolio')}>
                <i className="fa-solid fa-plus-circle" style={{ color: '#00b4aa', fontSize: '15px' }}></i>
                Add Property to Portfolio
              </div>
              <div className="suggestion-chip" onClick={() => triggerSuggestion('How much profit have I made on my real estate portfolio?')}>
                <i className="fa-solid fa-sack-dollar" style={{ color: '#00b4aa', fontSize: '15px' }}></i>
                Portfolio Profit & Growth
              </div>
            </div>

          </div>
        )}

        {/* Message Feed */}
        {messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.sender}`}>
            {msg.sender === 'reva' && (
              <div className="bot-avatar-container">
                <img src="/img/icons/chatbot.svg" alt="Reva" />
              </div>
            )}
            
            {msg.type === 'text' && (
              <div className="bubble" dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>') }} />
            )}

            {msg.type === 'prediction_form' && msg.extraData && (
              msg.extraData.model_type === 'house' ? (
                <HousePredictionFormCard data={msg.extraData} onSubmit={(prompt) => handleSendMessage(prompt)} />
              ) : msg.extraData.model_type === 'rental' ? (
                <RentalPredictionFormCard data={msg.extraData} onSubmit={(prompt) => handleSendMessage(prompt)} />
              ) : (
                <LandPredictionFormCard data={msg.extraData} onSubmit={(prompt) => handleSendMessage(prompt)} />
              )
            )}

            {msg.type === 'add_property_form' && msg.extraData && (
              msg.extraData.property_type === 'rental' ? (
                <AddRentalFormCard data={msg.extraData} onSubmit={(prompt) => handleSendMessage(prompt)} />
              ) : msg.extraData.property_type === 'land' ? (
                <AddLandFormCard data={msg.extraData} onSubmit={(prompt) => handleSendMessage(prompt)} />
              ) : (
                <AddHousingFormCard data={msg.extraData} onSubmit={(prompt) => handleSendMessage(prompt)} />
              )
            )}

            {msg.type === 'portfolio_overview' && msg.extraData && (
              <PortfolioSummaryCard
                summary={msg.extraData.summary}
                properties={msg.extraData.properties}
                onAction={(q) => handleSendMessage(q)}
              />
            )}

            {msg.type === 'add_property_success' && msg.extraData && (
              <AddPropertySuccessCard
                data={msg.extraData}
                onAction={(q) => handleSendMessage(q)}
              />
            )}

            {msg.type === 'full_analysis' && msg.extraData && (
              <FullAnalysisCard data={msg.extraData} onAskFollowup={(q) => handleSendMessage(q)} />
            )}

            {msg.type === 'prediction_result' && msg.extraData && (
              <div className="bubble">
                <div dangerouslySetInnerHTML={{ __html: msg.text }} />
                <div className="prediction-result">
                  <div className="pred-value">{msg.extraData.price}</div>
                  <div className="success-badge">
                    <i className="fa-solid fa-check-circle"></i> Range: {msg.extraData.range}
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-gray)', marginTop: '10px' }}>
                    <strong>Reasoning:</strong> {msg.extraData.reasoning}
                  </p>
                </div>
              </div>
            )}

            {msg.type === 'graph' && <PriceGraph />}

          </div>
        ))}


        {/* Typing Indicator */}
        {isTyping && (
          <div className="message-wrapper reva">
            <div className="bot-avatar-container loading">
              <img src="/img/icons/chatbot.svg" alt="Reva" />
            </div>
            <div className="typing-bubble"><span></span><span></span><span></span></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="input-bar-container">
        <div className="input-wrapper">
          <textarea 
            ref={textareaRef}
            className="chat-input" 
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(inputValue);
              }
            }}
            placeholder="Ask Reva about property prices..." 
            rows={1} 
          />
          <button
            type="button"
            className={`mic-button ${isListening ? 'listening' : ''}`}
            onClick={toggleSpeechToText}
            onPointerDown={handleMicPointerDown}
            onPointerUp={handleMicPointerUp}
            onPointerLeave={handleMicPointerUp}
            onPointerCancel={handleMicPointerUp}
            title={isListening ? 'Stop listening' : 'Start speaking'}
            aria-label={isListening ? 'Stop speech recognition' : 'Start speech recognition'}
          >
            <i className={`fa-solid ${isListening ? 'fa-microphone-lines' : 'fa-microphone'}`}></i>
          </button>
          <img src="/img/icons/send.svg" className="send-icon" alt="Send" onClick={() => handleSendMessage(inputValue)} />
        </div>
        {speechError && <div className="speech-error">{speechError}</div>}
      </div>
    </div>
  );
};

export default Askreva;

