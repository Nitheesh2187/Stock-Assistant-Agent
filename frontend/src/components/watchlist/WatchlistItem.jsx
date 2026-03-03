import { X } from 'lucide-react';

export default function WatchlistItem({ item, selected, onSelect, onRemove }) {
  return (
    <div
      onClick={() => onSelect(item.symbol, item.stock_name)}
      className={`flex items-center justify-between px-3 py-2.5 cursor-pointer transition-colors group ${
        selected
          ? 'bg-primary-100 dark:bg-primary-600/15 border-l-2 border-primary-600 dark:border-primary-400'
          : 'hover:bg-blue-100 dark:hover:bg-surface-800 border-l-2 border-transparent'
      }`}
    >
      <div className="min-w-0">
        <p className={`text-sm font-semibold truncate ${selected ? 'text-primary-700 dark:text-primary-400' : 'text-surface-900 dark:text-surface-100'}`}>
          {item.symbol}
        </p>
        <p className="text-xs text-surface-500 dark:text-surface-400 truncate">{item.stock_name}</p>
      </div>
      <button
        onClick={(e) => { e.stopPropagation(); onRemove(item.symbol); }}
        className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-blue-200 dark:hover:bg-surface-700 text-surface-400 dark:text-surface-500 hover:text-negative transition-all"
        aria-label={`Remove ${item.symbol}`}
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
