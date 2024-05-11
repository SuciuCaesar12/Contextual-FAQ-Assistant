import React, { useState } from "react";
import askQuestion from "../api.tsx";
import { ChatLog } from "./ChatLog.tsx";
import { ChatInput } from "./ChatInput.tsx";


export const ChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { sender: "bot", text: "Hello! How can I help you today?" },
  ]);
  const [typingMessage, setTypingMessage] = useState<string>("");

  const handleSendMessage = async () => {
    if (!typingMessage) {
      return;
    }

    setMessages([...messages, { sender: "user", text: typingMessage }]);
    setTypingMessage("");

    try {
      const response = await askQuestion(typingMessage);
      setMessages([
       ...messages,
        { sender: "user", text: typingMessage },
        { sender: "bot", text: response.answer },
      ]);
      console.log("Answer from backend: ", response.answer);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="h-screen p-4 flex flex-col">
      <ChatLog messages={messages} className="flex-grow overflow-y-auto" />
      <ChatInput
        value={typingMessage}
        onTyping={(e) => setTypingMessage(e.target.value)}
        onSubmit={handleSendMessage}
        className="w-full"
      />
    </div>
  );
};
