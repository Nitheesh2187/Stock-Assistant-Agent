import { useEffect, useRef } from 'react';
import { mapToTradingViewSymbol } from '../../utils/format';
import { useResizable } from '../../hooks/useResizable';

export default function TradingViewWidget({ symbol, dark }) {
  const containerRef = useRef(null);

  const { size: chartHeight, isDragging, handleMouseDown } = useResizable({
    direction: 'vertical',
    initialSize: 450,
    minSize: 450,
    maxSize: 800,
    storageKey: 'chart-height',
  });

  useEffect(() => {
    if (!symbol || !containerRef.current) return;

    const tvSymbol = mapToTradingViewSymbol(symbol);
    const container = containerRef.current;

    // Clear previous widget
    container.innerHTML = '';

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.type = 'text/javascript';
    script.async = true;
    script.innerHTML = JSON.stringify({
      width: '100%',
      height: '450',
      symbol: tvSymbol,
      interval: 'D',
      timezone: 'Asia/Kolkata',
      theme: dark ? 'dark' : 'light',
      style: '1',
      locale: 'en',
      allow_symbol_change: false,
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false,
      calendar: false,
      support_host: 'https://www.tradingview.com',
    });

    container.appendChild(script);

    return () => {
      container.innerHTML = '';
    };
  }, [symbol, dark]);

  return (
    <div className="relative">
      {/* Fixed overlay during drag */}
      {isDragging && <div className="fixed inset-0 z-50" />}
      <div
        ref={containerRef}
        className="tradingview-widget-container w-full rounded-lg overflow-hidden border border-surface-200 dark:border-surface-800"
        style={{ height: chartHeight }}
      />
      {/* Bottom drag handle */}
      <div
        onMouseDown={handleMouseDown}
        className="group flex items-center justify-center h-3 cursor-row-resize hover:bg-surface-200/60 dark:hover:bg-surface-700/60 transition-colors"
      >
        <div className="w-10 h-1 rounded-full bg-surface-300 dark:bg-surface-600 group-hover:bg-primary-400 transition-colors" />
      </div>
    </div>
  );
}
