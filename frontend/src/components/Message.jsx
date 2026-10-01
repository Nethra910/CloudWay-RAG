import { Bot, User, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function Message({ message }) {
  const isUser = message.role === "user";

  const uniqueSources = [...new Set(message.sources || [])];

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`flex max-w-[80%] gap-3 ${
          isUser ? "flex-row-reverse" : "flex-row"
        }`}
      >
        {/* Avatar */}
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
            isUser ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-700"
          }`}
        >
          {isUser ? <User size={18} /> : <Bot size={18} />}
        </div>

        {/* Message content */}
        <div>
          <div
            className={`rounded-2xl px-4 py-3 ${
              isUser
                ? "rounded-tr-sm bg-blue-600 text-white"
                : "rounded-tl-sm border border-slate-200 bg-white text-slate-700 shadow-sm"
            }`}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap text-sm leading-6">
                {message.content}
              </p>
            ) : (
              <div className="prose prose-sm prose-slate max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* Sources */}
          {!isUser && uniqueSources.length > 0 && (
            <div className="mt-2">
              <p className="mb-2 text-xs font-medium text-slate-500">Sources</p>

              <div className="flex flex-wrap gap-2">
                {uniqueSources.map((source, index) => {
                  const fileName = source.split("/").pop();

                  return (
                    <div
                      key={index}
                      className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600"
                    >
                      <FileText size={14} className="shrink-0 text-blue-600" />

                      <span>{fileName}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Message;
