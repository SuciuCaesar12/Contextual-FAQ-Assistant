interface ChatLogProps {
  messages: ChatMessage[];
  classname?: string;
}

export const ChatLog: React.FC<ChatLogProps & React.ComponentProps<'div'>> = ({ messages }) => {
  return (
    <div className="flex flex-col overflow-y-auto h-full">
      {messages.map((message, index) => (
        <div key={index} className={`flex ${message.sender === 'user'? 'justify-start' : 'justify-end'} mb-5`}>
          <span
            className={`px-4 py-2 rounded-md max-w-md
            ${message.sender === 'user'? 'bg-gray-200 text-gray-800' : 'bg-gray-600 text-white'}`}
          >
            {message.text}
          </span>
        </div>
      ))}
    </div>
  );
};