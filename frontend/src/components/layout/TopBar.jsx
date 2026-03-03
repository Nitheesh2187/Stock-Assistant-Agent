import { TrendingUp, Sun, Moon, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import Avatar from '../ui/Avatar';

export default function TopBar({ dark, onToggleDark }) {
  const { user, logout } = useAuth();

  return (
    <header className="relative h-14 flex items-center justify-center px-4 bg-surface-900 dark:bg-surface-900 border-b border-surface-800">
      <div className="flex items-center gap-2">
        <TrendingUp className="h-6 w-6 text-primary-400" />
        <span className="text-lg font-bold text-white">StockAssist</span>
      </div>
      <div className="absolute right-4 flex items-center gap-3">
        <button
          onClick={onToggleDark}
          className="p-2 rounded-lg hover:bg-surface-800 text-surface-300 hover:text-white transition-colors"
          aria-label="Toggle dark mode"
        >
          {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
        <Avatar name={user?.name} size="sm" />
        <button
          onClick={logout}
          className="p-2 rounded-lg hover:bg-surface-800 text-surface-300 hover:text-white transition-colors"
          aria-label="Logout"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}
