const Sidebar = () => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <span>rēva</span>
        </div>
      </div>

      <button className="new-chat-btn">
        <i className="fa-solid fa-plus"></i> New Chat
      </button>

      <div className="history-label">Recent</div>

      <ul className="history-list">
        <li className="history-item active">Land prices in Kandy</li>
        <li className="history-item">Apartment rentals Colombo 03</li>
      </ul>

      <div className="user-profile">
        <img src="https://i.pravatar.cc/150?img=68" />
        <div className="user-name">Sarah Perera</div>
      </div>
    </aside>
  );
};

export default Sidebar;