import { Cloud, Circle } from "lucide-react";

function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2">
          <Cloud className="h-7 w-7 text-blue-600" />

          <h1 className="text-xl font-bold text-slate-800">CloudWay AI</h1>
        </div>

        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Circle className="h-2.5 w-2.5 fill-green-500 text-green-500" />
          Online
        </div>
      </div>
    </header>
  );
}

export default Header;
