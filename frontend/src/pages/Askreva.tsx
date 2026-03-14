import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom'; // Assuming you use react-router
import '../assets/css/askreva.css'; // Make sure this path matches your setup

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


// --- Main Page Component ---

const Askreva: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

 const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const newUserMsg: Message = { id: Date.now().toString(), text, sender: 'user', type: 'text' };
    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');
    if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
    }
    setIsTyping(true);

    try {
      // Point directly to the FastAPI server on port 8000
      const response = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await response.json();
      
      const newBotMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: data.reply || "I'm sorry, I encountered an error processing that.",
        sender: 'reva',
        type: data.type || 'text',
        extraData: data
      };
      setMessages(prev => [...prev, newBotMsg]);
    } catch (error) {
      // Updated error message to accurately reflect FastAPI
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: "Could not connect to the Rēva server. Make sure your FastAPI server is running on port 8000.", sender: 'reva', type: 'text' }]);
    } finally {
      setIsTyping(false);
    }
  };

  const triggerSuggestion = (text: string) => {
    handleSendMessage(text);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', backgroundColor: 'var(--primary-bg)', fontFamily: 'fontRegular, sans-serif' }}>
      
      {/* Sidebar Overlays */}
      <div className={`sidebar-overlay ${isSidebarOpen ? 'show' : ''}`} onClick={() => setIsSidebarOpen(false)}></div>
      <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`} id="sidebar">
        <div className="sidebar-header">
          <h3>Previous Chats</h3>
          <i className="fa-solid fa-xmark" onClick={() => setIsSidebarOpen(false)} style={{ cursor: 'pointer' }}></i>
        </div>
        <ul className="chat-history" id="historyList">
            {/* Map history here later */}
        </ul>
      </div>

      {/* Header */}
      <header className="chat-header">
        <div className="header-left">
          <img src="/img/icons/bars.svg" className="hamburger-icon" alt="Menu" onClick={() => setIsSidebarOpen(true)} />
        </div>
        <div className="header-center">
          <Link to="/" className="back-btn"><i className="fa-solid fa-chevron-left"></i></Link>
          <span className="agent-name">Ask Rēva</span>
          <img src="/img/icons/chat.svg" alt="Chat" className="chat-icon" />
        </div>
        <div className="header-right">
          <img src="https://i.pravatar.cc/150?img=11" className="user-avatar" alt="User" />
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
                <img src="/img/icons/chatbot.svg" alt="Rēva" />
              </div>
            )}
            
            {msg.type === 'text' && (
              <div className="bubble" dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>') }} />
            )}

            {msg.type === 'prediction_form' && msg.extraData && (
              <PredictionFormCard data={msg.extraData} onSubmit={(prompt) => {
                  // Removed the duplicate setMessages call from here!
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
              <img src="/img/icons/chatbot.svg" alt="Rēva" />
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
            placeholder="Ask Rēva about property prices..." 
            rows={1} 
          />
          <img src="/img/icons/send.svg" className="send-icon" alt="Send" onClick={() => handleSendMessage(inputValue)} />
        </div>
      </div>
    </div>
  );
};

export default Askreva;