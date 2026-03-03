import client from './client';

export function getStockQuote(symbol) {
  return client.get(`/api/stocks/${encodeURIComponent(symbol)}/quote`);
}

export function getStockFundamentals(symbol) {
  return client.get(`/api/stocks/${encodeURIComponent(symbol)}/fundamentals`);
}

export function getStockNews(symbol, stockName, limit = 10) {
  return client.get(`/api/stocks/${encodeURIComponent(symbol)}/news`, {
    params: { stock_name: stockName, limit },
  });
}
