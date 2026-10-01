import { useState } from "react";
import { Send } from "lucide-react";

function ChatInput({ onAsk, loading }) {
  const [question, setQuestion] = useState("");

  const handleSubmit = () => {
    if (!question.trim() || loading) {
      return;
    }

    onAsk(question.trim());
    setQuestion("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <div className="mx-auto flex max-w-4xl items-end gap-3">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          rows="1"
          placeholder="Ask CloudWay anything..."
          className="max-h-32 min-h-12 flex-1 resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white disabled:opacity-50"
        />

        <button
          onClick={handleSubmit}
          disabled={loading || !question.trim()}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send size={18} />
        </button>
      </div>

      <p className="mt-2 text-center text-xs text-slate-400">
        Press Enter to send • Shift + Enter for a new line
      </p>
    </div>
  );
}

export default ChatInput;
