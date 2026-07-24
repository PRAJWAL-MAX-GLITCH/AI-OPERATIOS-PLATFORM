import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-end px-8 sticky top-0 z-10 shadow-sm">
      <div className="flex items-center space-x-4">
        <div className="text-sm text-right hidden sm:block">
          <p className="font-medium text-gray-900">{user?.name || 'User'}</p>
          <p className="text-gray-500 text-xs">{user?.email}</p>
        </div>
        <div className="h-9 w-9 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold border border-primary-200">
          {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
        </div>
      </div>
    </header>
  );
}
