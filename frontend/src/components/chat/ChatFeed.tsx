import MessageBubble from "./MessageBubble";

const ChatFeed = () => {
  return (
    <div className="chat-feed">
      <div className="empty-state">
        <h1>Hello, Sarah</h1>
        <p>How can I help you with real estate today?</p>
      </div>

      <MessageBubble
        type="user"
        text="What is the estimated price for a 10 perch land in Malabe?"
      />

      <MessageBubble
        type="ai"
        text="Based on current market trends, estimated LKR 1.8M - 2.5M per perch."
      />
    </div>
  );
};

export default ChatFeed;