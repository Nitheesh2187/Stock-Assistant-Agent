import { useContext, useCallback } from 'react';
import { useDarkMode } from '../hooks/useDarkMode';
import { useWatchlist } from '../hooks/useWatchlist';
import { StockContext } from '../contexts/StockContext';
import DashboardLayout from '../components/layout/DashboardLayout';
import WatchlistPanel from '../components/watchlist/WatchlistPanel';
import CenterContent from '../components/stock/CenterContent';
import ChatPanel from '../components/chat/ChatPanel';

export default function DashboardPage() {
  const { dark, toggle } = useDarkMode();
  const { items, loading, add, remove } = useWatchlist();
  const { selectedSymbol, clearSelectedStock } = useContext(StockContext);

  const handleRemove = useCallback(async (symbol) => {
    await remove(symbol);
    if (symbol === selectedSymbol) {
      clearSelectedStock();
    }
  }, [remove, selectedSymbol, clearSelectedStock]);

  return (
    <DashboardLayout
      dark={dark}
      onToggleDark={toggle}
      sidebar={
        <WatchlistPanel
          items={items}
          loading={loading}
          onAdd={add}
          onRemove={handleRemove}
          dark={dark}
          onToggleDark={toggle}
        />
      }
      center={<CenterContent dark={dark} />}
      chat={<ChatPanel />}
    />
  );
}
