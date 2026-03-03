import { useState, useEffect, useCallback } from 'react';
import { getWatchlist, addToWatchlist, removeFromWatchlist } from '../api/watchlist';
import toast from 'react-hot-toast';

export function useWatchlist() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const { data } = await getWatchlist();
      setItems(data);
    } catch {
      toast.error('Failed to load watchlist');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  const add = useCallback(async (symbol, stockName) => {
    try {
      const { data } = await addToWatchlist(symbol, stockName);
      setItems((prev) => [...prev, data]);
      toast.success(`${symbol} added to watchlist`);
      return data;
    } catch (err) {
      const msg = err.response?.status === 409 ? 'Already in watchlist' : 'Failed to add';
      toast.error(msg);
      throw err;
    }
  }, []);

  const remove = useCallback(async (symbol) => {
    try {
      await removeFromWatchlist(symbol);
      setItems((prev) => prev.filter((item) => item.symbol !== symbol));
      toast.success(`${symbol} removed`);
    } catch {
      toast.error('Failed to remove');
    }
  }, []);

  return { items, loading, add, remove, refresh: fetch };
}
