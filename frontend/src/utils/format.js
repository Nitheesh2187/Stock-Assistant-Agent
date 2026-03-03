export function formatCurrency(value, currency = 'USD') {
  const num = parseFloat(value);
  if (isNaN(num)) return value ?? '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(num);
}

export function formatPercent(value) {
  const num = parseFloat(value);
  if (isNaN(num)) return value ?? '—';
  const sign = num >= 0 ? '+' : '';
  return `${sign}${num.toFixed(2)}%`;
}

export function formatLargeNumber(value) {
  const num = parseFloat(value);
  if (isNaN(num)) return value ?? '—';
  if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
  return num.toFixed(2);
}

export function mapToTradingViewSymbol(symbol) {
  if (!symbol) return '';
  if (symbol.endsWith('.NS')) return `NSE:${symbol.replace('.NS', '')}`;
  if (symbol.endsWith('.BO')) return `BSE:${symbol.replace('.BO', '')}`;
  return symbol;
}
