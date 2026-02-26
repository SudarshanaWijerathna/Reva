type Props = {
  type: "user" | "ai";
  text: string;
};

const MessageBubble = ({ type, text }: Props) => {
  return (
    <div className={`message ${type}`}>
      <div className={`avatar ${type === "ai" ? "ai-avatar" : "user-avatar"}`}>
        {type === "ai" ? (
          <img src="/img/university-logo.png" />
        ) : (
          <img src="https://i.pravatar.cc/150?img=68" />
        )}
      </div>

      <div
        className="bubble"
        dangerouslySetInnerHTML={{ __html: text }}
      ></div>
    </div>
  );
};

export default MessageBubble;