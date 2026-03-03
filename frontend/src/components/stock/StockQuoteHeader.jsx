import { formatCurrency, formatPercent, formatLargeNumber } from '../../utils/format';

export default function StockQuoteHeader({ symbol, stockName, quote }) {
  // Handle various API response shapes from Alpha Vantage / MCP tools
  const price = quote?.price || quote?.['05. price'] || quote?.currentPrice || quote?.['Global Quote']?.['05. price'];
  const change = quote?.change || quote?.['09. change'] || quote?.['Global Quote']?.['09. change'];
  const changePercent = quote?.change_percent || quote?.['10. change percent'] || quote?.changePercent || quote?.['Global Quote']?.['10. change percent'];
  const volume = quote?.volume || quote?.['06. volume'] || quote?.['Global Quote']?.['06. volume'];

  const numChange = parseFloat(change);
  const isPositive = !isNaN(numChange) && numChange >= 0;

  return (
    <div className="px-4 pt-4 pb-2 mx-4 mt-2 rounded-lg bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800">
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-xl font-bold text-surface-900 dark:text-surface-100">{symbol}</h1>
        {stockName && (
          <span className="text-sm text-surface-500 dark:text-surface-400">{stockName}</span>
        )}
        {price && (
          <span className="text-xl font-bold text-surface-900 dark:text-surface-100 ml-auto">
            {formatCurrency(price)}
          </span>
        )}
        {change && !isNaN(numChange) && (
          <span className={`text-sm font-semibold ${isPositive ? 'text-positive' : 'text-negative'}`}>
            {isPositive ? '+' : ''}{numChange.toFixed(2)}
          </span>
        )}
        {changePercent && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            isPositive ? 'bg-green-100 text-positive dark:bg-green-900/30' : 'bg-red-100 text-negative dark:bg-red-900/30'
          }`}>
            {formatPercent(parseFloat(String(changePercent).replace('%', '')))}
          </span>
        )}
        {volume && (
          <span className="text-xs text-surface-500 dark:text-surface-400">
            Vol: {formatLargeNumber(volume)}
          </span>
        )}
      </div>
    </div>
  );
}
