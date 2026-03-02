import { useState } from "react";

const ChatInput = () => {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="input-container">
      <div className="prompt-box">
        <div className={`action-menu ${menuOpen ? "active" : ""}`}>
          <div className="menu-item">
            <i className="fa-solid fa-house-chimney"></i>
            Attach my properties
          </div>
        </div>

        <button
          className={`action-btn ${menuOpen ? "active" : ""}`}
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <i className="fa-solid fa-plus"></i>
        </button>

        <textarea placeholder="Ask Reva about properties..." />

        <button className="action-btn send-btn">
          <i className="fa-solid fa-paper-plane"></i>
        </button>
      </div>

      <div className="disclaimer">
        Reva can make mistakes. Consider checking important information.
      </div>
    </div>
  );
};

export default ChatInput;