import { useContext } from 'react';
import { TrendingUp, LogOut, Sun, Moon } from 'lucide-react';
import { StockContext } from '../../contexts/StockContext';
import { useAuth } from '../../hooks/useAuth';
import StockSearch from './StockSearch';
import WatchlistItem from './WatchlistItem';
import Spinner from '../ui/Spinner';
import Avatar from '../ui/Avatar';

export default function WatchlistPanel({ items, loading, onAdd, onRemove, dark, onToggleDark }) {
  const { selectedSymbol, setSelectedStock } = useContext(StockContext);
  const { user, logout } = useAuth();

  return (
    <div className="flex flex-col h-full bg-blue-50 dark:bg-surface-900">
      {/* Branding */}
      <div className="flex items-center gap-2 px-3 py-3">
        <TrendingUp className="h-5 w-5 text-primary-600 dark:text-primary-400" />
        <span className="text-lg font-bold text-surface-900 dark:text-white">StockAssist</span>
      </div>

      {/* Search */}
      <div className="p-3 border-t border-blue-100 dark:border-surface-700">
        <StockSearch onAdd={onAdd} />
      </div>

      {/* Stock list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : items.length === 0 ? (
          <div className="p-4 text-center text-sm text-surface-500 dark:text-surface-400">
            Search and add stocks to your watchlist.
          </div>
        ) : (
          items.map((item) => (
            <WatchlistItem
              key={item.symbol}
              item={item}
              selected={item.symbol === selectedSymbol}
              onSelect={setSelectedStock}
              onRemove={onRemove}
            />
          ))
        )}
      </div>

      {/* Account bar at bottom */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-t border-blue-100 dark:border-surface-700">
        <Avatar name={user?.name} size="sm" />
        <span className="flex-1 text-sm font-medium text-surface-800 dark:text-surface-200 truncate">
          {user?.name || 'Account'}
        </span>
        {onToggleDark && (
          <button
            onClick={onToggleDark}
            className="p-1.5 rounded-md hover:bg-blue-100 dark:hover:bg-surface-800 text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 transition-colors"
            aria-label="Toggle dark mode"
          >
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        )}
        <button
          onClick={logout}
          className="p-1.5 rounded-md hover:bg-blue-100 dark:hover:bg-surface-800 text-surface-500 dark:text-surface-400 hover:text-negative transition-colors"
          aria-label="Logout"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
