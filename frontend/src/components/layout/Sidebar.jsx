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
  Activity,
  Settings,
  LogOut
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { clsx } from 'clsx';

const NAVIGATION = [
  { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { name: 'Projects', to: '/projects', icon: FolderGit2 },
  { name: 'Datasets', to: '/datasets', icon: Database },
  { name: 'Models', to: '/models', icon: Brain },
  { name: 'Experiments', to: '/experiments', icon: FlaskConical },
  { name: 'RAG Knowledge', to: '/rag', icon: FileText },
  { name: 'Chat', to: '/chat', icon: MessageSquare },
  { name: 'Agents', to: '/agents', icon: Bot },
  { name: 'Monitoring', to: '/monitoring', icon: Activity },
];

export default function Sidebar() {
  const { logout } = useAuth();

  return (
    <div className="flex flex-col w-64 bg-sidebar border-r border-gray-800 text-gray-300 h-screen sticky top-0">
      <div className="flex items-center justify-center h-16 px-4 border-b border-gray-800">
        <Brain className="w-8 h-8 text-primary-500 mr-2" />
        <span className="text-lg font-bold text-white tracking-wide">Enterprise AI</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAVIGATION.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.to}
              className={({ isActive }) => clsx(
                'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors group',
                isActive 
                  ? 'bg-primary-600 text-white' 
                  : 'hover:bg-gray-800 hover:text-white'
              )}
            >
              <Icon className="w-5 h-5 mr-3 flex-shrink-0" />
              {item.name}
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-800 space-y-2">
        <NavLink
          to="/settings"
          className={({ isActive }) => clsx(
            'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
            isActive ? 'bg-primary-600 text-white' : 'hover:bg-gray-800 hover:text-white'
          )}
        >
          <Settings className="w-5 h-5 mr-3" />
          Settings
        </NavLink>
        <button
          onClick={logout}
          className="flex items-center w-full px-3 py-2 text-sm font-medium rounded-md text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
        >
          <LogOut className="w-5 h-5 mr-3" />
          Sign out
        </button>
      </div>
    </div>
  );
}
