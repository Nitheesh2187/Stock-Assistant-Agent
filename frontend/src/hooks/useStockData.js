import { useState, useEffect } from 'react';
import { getStockQuote, getStockFundamentals, getStockNews } from '../api/stocks';

function unwrapMcpResponse(payload) {
  if (payload && typeof payload === 'object' && 'success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload;
}

export function useStockData(symbol, stockName) {
  const [quote, setQuote] = useState(null);
  const [fundamentals, setFundamentals] = useState(null);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!symbol) {
      setQuote(null);
      setFundamentals(null);
      setNews([]);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.allSettled([
      getStockQuote(symbol),
      getStockFundamentals(symbol),
      getStockNews(symbol, stockName || symbol),
    ]).then(([quoteRes, fundRes, newsRes]) => {
      if (cancelled) return;
      if (quoteRes.status === 'fulfilled') setQuote(unwrapMcpResponse(quoteRes.value.data));
      if (fundRes.status === 'fulfilled') setFundamentals(unwrapMcpResponse(fundRes.value.data));
      if (newsRes.status === 'fulfilled') setNews(unwrapMcpResponse(newsRes.value.data));
      setLoading(false);
    });

    return () => { cancelled = true; };
  }, [symbol, stockName]);

  return { quote, fundamentals, news, loading, error };
}
