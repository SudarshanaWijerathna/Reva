import BackgroundOverlay from "../components/chat/BackgroundOverlay";
import Sidebar from "../components/chat/Sidebar";
import ChatHeader from "../components/chat/ChatHeader";
import ChatFeed from "../components/chat/ChatFeed";
import ChatInput from "../components/chat/ChatInput";

import "../assets/css/chatbot.css";

const Chatbot = () => {
  return (
    <>
      <BackgroundOverlay />

      <div className="app-container">
        <Sidebar />

        <main className="main-chat">
          <ChatHeader />
          <ChatFeed />
          <ChatInput />
        </main>
      </div>
    </>
  );
};

export default Chatbot;