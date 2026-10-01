import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function Answer({ answer }) {
  if (!answer) {
    return null;
  }

  return (
    <div className="mt-10 w-full max-w-3xl">
      <h2 className="mb-3 text-lg font-semibold text-slate-800">Answer</h2>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="prose prose-slate max-w-none text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default Answer;
