import Message from "./Message";

function ChatWindow({ messages, loading }) {
  return (
    <div className="flex flex-1 flex-col gap-5 overflow-y-auto px-4 py-6">
      {messages.length === 0 && (
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-slate-800">
              How can I help you?
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Ask me anything about CloudWay.
            </p>
          </div>
        </div>
      )}

      {messages.map((message, index) => (
        <Message key={index} message={message} />
      ))}

      {loading && (
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200">
            🤖
          </div>

          <div className="rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-5 py-3 shadow-sm">
            <div className="flex gap-1">
              <span className="animate-bounce">●</span>
              <span className="animate-bounce [animation-delay:150ms]">●</span>
              <span className="animate-bounce [animation-delay:300ms]">●</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatWindow;
