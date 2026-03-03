import { useContext, useState, useCallback, useEffect, useRef } from 'react';
import { BarChart3 } from 'lucide-react';
import { StockContext } from '../../contexts/StockContext';
import { useStockData } from '../../hooks/useStockData';
import { useResizable } from '../../hooks/useResizable';
import StockQuoteHeader from './StockQuoteHeader';
import TradingViewWidget from './TradingViewWidget';
import FinancialTabs from './FinancialTabs';
import NewsSection from './NewsSection';
import EmptyState from '../ui/EmptyState';
import Spinner from '../ui/Spinner';

const STORAGE_KEY = 'financials-split';
const DEFAULT_RATIO = 0.55;
const MIN_RATIO = 0.2;
const MAX_RATIO = 0.8;

function useSplitRatio() {
  const [ratio, setRatio] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = parseFloat(stored);
      if (!isNaN(parsed) && parsed >= MIN_RATIO && parsed <= MAX_RATIO) return parsed;
    }
    return DEFAULT_RATIO;
  });

  const isDraggingRef = useRef(false);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(ratio));
  }, [ratio]);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);
    document.body.classList.add('resizing');
    document.body.style.cursor = 'row-resize';
  }, []);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDraggingRef.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const y = e.clientY - rect.top;
      const newRatio = Math.min(MAX_RATIO, Math.max(MIN_RATIO, y / rect.height));
      setRatio(newRatio);
    };

    const handleMouseUp = () => {
      if (!isDraggingRef.current) return;
      isDraggingRef.current = false;
      setIsDragging(false);
      document.body.classList.remove('resizing');
      document.body.style.cursor = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  return { ratio, isDragging, handleMouseDown, containerRef };
}

export default function CenterContent({ dark }) {
  const { selectedSymbol, selectedStockName } = useContext(StockContext);
  const { quote, fundamentals, news, loading } = useStockData(selectedSymbol, selectedStockName);
  const split = useSplitRatio();

  const dataHeightResize = useResizable({
    direction: 'vertical',
    initialSize: 600,
    minSize: 300,
    maxSize: 1000,
    storageKey: 'data-section-height',
  });

  if (!selectedSymbol) {
    return (
      <EmptyState
        icon={BarChart3}
        title="Select a stock"
        description="Choose a stock from your watchlist to view charts, financials, and news."
      />
    );
  }

  const hasFundamentals = fundamentals && typeof fundamentals === 'object' && Object.keys(fundamentals).length > 0;
  const hasNews = news && ((Array.isArray(news) && news.length > 0) || (!Array.isArray(news) && typeof news === 'object'));
  const showBothSections = hasFundamentals && hasNews;

  return (
    <div className="h-full overflow-y-auto bg-surface-100 dark:bg-surface-950">
      <StockQuoteHeader symbol={selectedSymbol} stockName={selectedStockName} quote={quote} />

      <div className="px-4 pt-4">
        <TradingViewWidget symbol={selectedSymbol} dark={dark} />
      </div>

      {loading && !hasFundamentals && !hasNews ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : showBothSections ? (
        <div className="px-4 pt-4 pb-2">
          {(split.isDragging || dataHeightResize.isDragging) && <div className="fixed inset-0 z-50" />}
          <div
            ref={split.containerRef}
            className="flex flex-col"
            style={{ height: dataHeightResize.size }}
          >
            <div
              className="overflow-auto min-h-0"
              style={{ flex: `${split.ratio} 1 0%` }}
            >
              <FinancialTabs fundamentals={fundamentals} />
            </div>
            <div
              onMouseDown={split.handleMouseDown}
              className="group flex-shrink-0 flex items-center justify-center h-3 cursor-row-resize hover:bg-surface-200/60 dark:hover:bg-surface-700/60 transition-colors"
            >
              <div className="w-10 h-1 rounded-full bg-surface-300 dark:bg-surface-600 group-hover:bg-primary-400 transition-colors" />
            </div>
            <div
              className="overflow-auto min-h-0"
              style={{ flex: `${1 - split.ratio} 1 0%` }}
            >
              <NewsSection news={news} />
            </div>
          </div>
          <div
            onMouseDown={dataHeightResize.handleMouseDown}
            className="group flex items-center justify-center h-3 cursor-row-resize hover:bg-surface-200/60 dark:hover:bg-surface-700/60 transition-colors"
          >
            <div className="w-10 h-1 rounded-full bg-surface-300 dark:bg-surface-600 group-hover:bg-primary-400 transition-colors" />
          </div>
        </div>
      ) : (
        <div className="px-4 pt-4 pb-6">
          {hasFundamentals && <FinancialTabs fundamentals={fundamentals} />}
          {hasNews && <div className={hasFundamentals ? 'mt-4' : ''}><NewsSection news={news} /></div>}
          {loading && <div className="flex justify-center py-4"><Spinner /></div>}
        </div>
      )}
    </div>
  );
}
