import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FolderGit2, 
  Database, 
  Brain, 
  FlaskConical, 
  FileText, 
  MessageSquare,
  Bot,
  History,
  Activity,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  GitBranch,
  Settings2,
  Sliders,
  Terminal,
  ActivitySquare
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { clsx } from 'clsx';

const NAVIGATION_GROUPS = [
  {
    group: 'Platform',
    items: [
      { name: 'Overview', to: '/dashboard', icon: LayoutDashboard },
    ]
  },
  {
    group: 'Workspace',
    items: [
      { name: 'Projects', to: '/projects', icon: FolderGit2 },
      { name: 'Datasets', to: '/datasets', icon: Database },
    ]
  },
  {
    group: 'Machine Learning',
    items: [
      { name: 'Models', to: '/models', icon: Brain },
      { name: 'Experiments', to: '/experiments', icon: FlaskConical },
    ]
  },
  {
    group: 'Cognitive AI',
    items: [
      { name: 'RAG Knowledge', to: '/rag', icon: FileText },
      { name: 'Chat Assistant', to: '/chat', icon: MessageSquare },
      { name: 'AI Agents', to: '/agents', icon: Bot },
      { name: 'Agent Runs', to: '/agents/history', icon: History, indent: true },
    ]
  },
  {
    group: 'Operations',
    items: [
      { name: 'Monitoring', to: '/monitoring', icon: Activity },
    ]
  }
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={clsx(
      "flex flex-col bg-slate-950 border-r border-slate-900 text-slate-300 h-screen sticky top-0 transition-all duration-300 select-none z-20",
      collapsed ? "w-16" : "w-64"
    )}>
      {/* Brand header */}
      <div className="flex items-center justify-between h-14 px-4 border-b border-slate-900/60">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-white flex items-center justify-center">
              <span className="text-black font-extrabold text-xs">AG</span>
            </div>
            <span className="text-xs font-bold text-white tracking-wider uppercase">Antigravity</span>
          </div>
        )}
        {collapsed && (
          <div className="mx-auto h-6 w-6 rounded bg-white flex items-center justify-center">
            <span className="text-black font-extrabold text-[10px]">AG</span>
          </div>
        )}
        <button 
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded text-slate-500 hover:text-white hover:bg-slate-900 transition-colors"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Navigation list */}
      <nav className="flex-1 px-3 py-4 space-y-4 overflow-y-auto">
        {NAVIGATION_GROUPS.map((group) => (
          <div key={group.group} className="space-y-1">
            {!collapsed && (
              <span className="block px-3 text-[9px] font-bold text-slate-600 uppercase tracking-widest mb-1.5">
                {group.group}
              </span>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.to}
                  end={item.to === '/agents'}
                  title={collapsed ? item.name : undefined}
                  className={({ isActive }) => clsx(
                    'flex items-center py-1.5 text-xs font-medium rounded transition-all duration-150 group',
                    collapsed ? 'justify-center px-1' : (item.indent ? 'pl-7 pr-3' : 'px-3'),
                    isActive 
                      ? 'bg-slate-900 text-white border border-slate-800' 
                      : 'hover:bg-slate-900/50 hover:text-white border border-transparent',
                    item.indent && !isActive && 'text-slate-500'
                  )}
                >
                  <Icon className={clsx(collapsed ? 'w-4 h-4' : 'mr-2.5 flex-shrink-0', item.indent ? 'w-3.5 h-3.5' : 'w-4 h-4')} />
                  {!collapsed && <span>{item.name}</span>}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Settings / User Footer */}
      <div className="p-3 border-t border-slate-900 space-y-1">
        <NavLink
          to="/settings"
          title={collapsed ? "Settings" : undefined}
          className={({ isActive }) => clsx(
            'flex items-center py-1.5 text-xs font-medium rounded transition-all duration-150',
            collapsed ? 'justify-center' : 'px-3',
            isActive ? 'bg-slate-900 text-white' : 'hover:bg-slate-900/50 hover:text-white'
          )}
        >
          <Settings2 className="w-4 h-4 mr-2.5 flex-shrink-0" />
          {!collapsed && <span>Settings</span>}
        </NavLink>
        
        <button
          onClick={logout}
          title={collapsed ? "Sign out" : undefined}
          className={clsx(
            "flex items-center w-full py-1.5 text-xs font-medium rounded text-slate-500 hover:text-rose-400 hover:bg-slate-900/30 transition-all duration-150",
            collapsed ? 'justify-center' : 'px-3'
          )}
        >
          <LogOut className="w-4 h-4 mr-2.5 flex-shrink-0" />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </div>
  );
}

