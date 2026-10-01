import { FileText } from "lucide-react";

function Sources({ sources }) {
  if (!sources || sources.length === 0) {
    return null;
  }

  const uniqueSources = [...new Set(sources)];

  return (
    <div className="mt-6 w-full max-w-3xl">
      <h2 className="mb-3 text-lg font-semibold text-slate-800">Sources</h2>

      <div className="space-y-2">
        {uniqueSources.map((source, index) => {
          const fileName = source.split("/").pop();

          return (
            <div
              key={index}
              className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm"
            >
              <FileText size={18} className="shrink-0 text-blue-600" />

              <span>{fileName}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default Sources;
