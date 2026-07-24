import { useAuth } from '../../context/AuthContext';
import { Search, Bell, Command, Sun } from 'lucide-react';

export default function Navbar() {
  const { user } = useAuth();

  return (
    <header className="h-14 bg-white border-b border-slate-200/80 flex items-center justify-between px-6 sticky top-0 z-10 select-none">
      {/* Search / Breadcrumbs area */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-slate-100/70 border border-slate-200/60 text-slate-400 text-xs w-64 cursor-pointer hover:bg-slate-100 transition-colors">
          <Search className="w-3.5 h-3.5" />
          <span className="flex-1 text-left text-slate-500 font-medium text-[11px]">Search workspace...</span>
          <span className="flex items-center gap-0.5 text-[9px] font-bold text-slate-400 bg-white border border-slate-200 rounded px-1 py-0.5">
            <Command className="w-2.5 h-2.5" /> K
          </span>
        </div>
      </div>

      {/* User profile controls & notification area */}
      <div className="flex items-center space-x-3.5">
        <button className="p-1.5 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors">
          <Bell className="w-4 h-4" />
        </button>

        <div className="h-4 w-px bg-slate-200"></div>

        <div className="flex items-center space-x-2">
          <div className="text-right hidden sm:block">
            <p className="font-semibold text-slate-800 text-xs">{user?.username || 'Operator'}</p>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">{user?.role || 'Viewer'}</p>
          </div>
          <div className="h-7 w-7 rounded bg-slate-900 flex items-center justify-center text-white text-xs font-bold shadow-sm">
            {user?.username ? user.username.charAt(0).toUpperCase() : 'U'}
          </div>
        </div>
      </div>
    </header>
  );
}
