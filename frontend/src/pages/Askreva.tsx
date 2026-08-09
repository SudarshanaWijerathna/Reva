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
  extracted?: {
    district: string;
    area: string;
    size: string;
    road: string;
    utilities: string;
  };
  price?: string;
  range?: string;
  reasoning?: string;
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'reva';
  type: 'text' | 'prediction_form' | 'prediction_result' | 'graph';
  extraData?: ExtraData;
}

// --- Sub-Components for Complex Messages ---

const PredictionFormCard: React.FC<{ data: ExtraData, onSubmit: (prompt: string) => void }> = ({ data, onSubmit }) => {
  const [step, setStep] = useState(1);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const ex = data.extracted || { district: '', area: '', size: '', road: '', utilities: '' };

  const [form, setForm] = useState({
    district: ex.district || '',
    area: ex.area || '',
    size: ex.size || '',
    hasRoad: Boolean(ex.road && ex.road !== 'None'), 
    roadValue: ex.road && ex.road !== 'None' ? ex.road : '',
    utilities: ex.utilities || ''
  });

  const handleUtilChange = (val: string) => {
    const currentUtils = form.utilities.split(', ').filter(Boolean);
    if (currentUtils.includes(val)) {
      setForm({ ...form, utilities: currentUtils.filter(u => u !== val).join(', ') });
    } else {
      setForm({ ...form, utilities: [...currentUtils, val].join(', ') });
    }
  };

  const hasUtil = (val: string) => form.utilities.toLowerCase().includes(val.toLowerCase());

  const handleSubmit = () => {
    setIsSubmitted(true);
    const roadAccess = form.hasRoad ? (form.roadValue || 'Available') : 'No specific road access';
    const utils = form.utilities || 'None';
    const prompt = `Please estimate the price for a ${form.size || '0'} perch land in ${form.area || 'Unknown'}, ${form.district || 'Unknown'}. Utilities: ${utils}. Road access: ${roadAccess}.`;
    onSubmit(prompt);
  };

  return (
    <div className="bubble">
      <p>I need a few more details to give you an accurate estimate.</p>
      <hr className="chat-divider" />
      
      <div className={`form-step form-step-1 ${step === 1 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div className="input-group">
              <label>District</label>
              <select className="input-field f-dist" value={form.district} onChange={e => setForm({...form, district: e.target.value})} disabled={isSubmitted}>
                <option value="" disabled>Select District</option>
                <option value="Colombo">Colombo</option>
                <option value="Kaluthara">Kaluthara</option>
                <option value="Gampaha">Gampaha</option>
              </select>
            </div>
            <div className="input-group">
              <label>Area / Town</label>
              <input type="text" className="input-field f-area" value={form.area} onChange={e => setForm({...form, area: e.target.value})} placeholder="e.g. Maharagama" readOnly={isSubmitted} />
            </div>
            <div className="input-group">
              <label>Land size (perches)</label>
              <input type="number" className="input-field f-size" value={form.size} onChange={e => setForm({...form, size: e.target.value})} placeholder="e.g. 20" readOnly={isSubmitted} />
            </div>
            <div style={{ marginTop: '5px' }}>
              <button className="cta-btn" onClick={() => setStep(2)} disabled={isSubmitted}>Next Step &nbsp;<i className="fa-solid fa-arrow-right"></i></button>
            </div>
          </div>
        </div>
      </div>

      <div className={`form-step form-step-2 ${step === 2 ? 'active' : ''}`}>
        <div className="form-step-inner">
          <div className="form-layout">
            <div className="input-group">
              <label>Other utilities</label>
              <div className="checkbox-grid">
                {['Main road', 'Electricity', 'Clear deed', 'Water', 'Bank loan', 'Near town'].map(util => (
                  <label key={util} className={`checkbox-item ${isSubmitted ? 'disabled' : ''}`}>
                    <input type="checkbox" className="f-util" value={util} checked={hasUtil(util)} onChange={() => handleUtilChange(util)} disabled={isSubmitted} />
                    <span className="checkmark"></span> {util}
                  </label>
                ))}
              </div>
            </div>
            <div className="input-group">
              <label className="checkbox-item" style={{ marginBottom: '12px', fontWeight: 600, color: 'var(--primary-dark)' }}>
                <input type="checkbox" className="f-road-toggle" checked={form.hasRoad} onChange={e => setForm({...form, hasRoad: e.target.checked})} disabled={isSubmitted} />
                <span className="checkmark"></span> Road Access Available
              </label>
              <input type="text" className="input-field f-road" value={form.roadValue} onChange={e => setForm({...form, roadValue: e.target.value})} placeholder="e.g. 15ft or 200m" disabled={!form.hasRoad || isSubmitted} />
            </div>
            <div style={{ display: 'flex', gap: '10px', marginTop: '5px' }}>
              <button className="btn-outline" onClick={() => setStep(1)} style={{ flex: 1 }} disabled={isSubmitted}>Back</button>
              <button className="cta-btn" style={{ flex: 2 }} onClick={handleSubmit} disabled={isSubmitted}>
                {isSubmitted ? <><i className="fa-solid fa-check"></i> Estimated</> : 'Estimate Price'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const PriceGraph: React.FC = () => (
  <div className="bubble">
    <p>Here is the price trend visualization you requested.</p>
    <div className="chat-chart-container">
      <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '10px', fontFamily: 'fontExtraBold' }}>Price Trend (LKR)</div>
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
            <h2>What can I help with?</h2>
            <div className="suggestion-grid">
              <div className="suggestion-chip" onClick={() => triggerSuggestion('predict a price of a house near moratuwa with 200m to the main road and electricity available')}>
                <img src="/img/icons/house.svg" alt="House" />
                House price prediction
              </div>
              <div className="suggestion-chip" onClick={() => triggerSuggestion('I need a rental price prediction')}>
                <img src="/img/icons/rental.svg" alt="Rental" />
                Rental price prediction
              </div>
              <div className="suggestion-chip" onClick={() => triggerSuggestion('I need a land price prediction')}>
                <img src="/img/icons/land.svg" alt="Land" />
                Land price prediction
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
              <PredictionFormCard data={msg.extraData} onSubmit={(prompt) => {
                  handleSendMessage(prompt);
              }} />
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
                  <p style={{ fontSize: '13px', marginTop: '15px', fontWeight: 600 }}>
                    Would you like me to generate a visualization of the price trends for this area over the last 3 years?
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

