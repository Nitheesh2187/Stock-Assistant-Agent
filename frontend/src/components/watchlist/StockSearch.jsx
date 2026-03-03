import { useState, useRef, useEffect } from 'react';
import { Search, Plus } from 'lucide-react';
import { searchStocks } from '../../api/watchlist';
import Spinner from '../ui/Spinner';

export default function StockSearch({ onAdd }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const timerRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleChange = (e) => {
    const val = e.target.value;
    setQuery(val);

    if (timerRef.current) clearTimeout(timerRef.current);

    if (val.trim().length < 1) {
      setResults([]);
      setOpen(false);
      return;
    }

    timerRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const { data } = await searchStocks(val.trim());
        setResults(data);
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 400);
  };

  const handleSelect = (stock) => {
    onAdd(stock.symbol, stock.name);
    setQuery('');
    setResults([]);
    setOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-400 dark:text-surface-500" />
        <input
          type="text"
          value={query}
          onChange={handleChange}
          placeholder="Search stocks..."
          className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-blue-200 dark:border-surface-600 bg-white dark:bg-surface-800 text-surface-900 dark:text-surface-100 placeholder-surface-400 dark:placeholder-surface-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        {loading && <Spinner size="sm" className="absolute right-3 top-1/2 -translate-y-1/2" />}
      </div>

      {open && results.length > 0 && (
        <div className="absolute z-20 mt-1 w-full bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {results.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => handleSelect(stock)}
              className="w-full flex items-center justify-between px-3 py-2 hover:bg-surface-50 dark:hover:bg-surface-700 text-left"
            >
              <div>
                <span className="text-sm font-medium text-surface-900 dark:text-surface-100">{stock.symbol}</span>
                <span className="text-xs text-surface-500 dark:text-surface-400 ml-2 truncate">{stock.name}</span>
              </div>
              <Plus className="h-4 w-4 text-primary-600 shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
