interface ChatInputProps {
  value: string;
  onTyping: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: () => void;
}

export const ChatInput: React.FC<ChatInputProps & React.ComponentProps<'div'>> = ({
  value,
  onTyping,
  onSubmit,
}) => {
  return (
    <div className="flex items-center justify-between w-full mb-4 space-x-1">
      <input
        type="text"
        value={value}
        onChange={onTyping}
        placeholder="Type your message..."
        aria-label="Chat input"
        className="w-full px-4 py-2 border border-gray-300 rounded-md"
      />
      <button
        type="button"
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md"
        onClick={onSubmit}
        role="button"
      >
        Send
      </button>
    </div>
  );
};