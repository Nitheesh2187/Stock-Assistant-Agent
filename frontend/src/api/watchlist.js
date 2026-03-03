import client from './client';

export function getWatchlist() {
  return client.get('/api/watchlist/');
}

export function addToWatchlist(symbol, stock_name) {
  return client.post('/api/watchlist/', { symbol, stock_name });
}

export function removeFromWatchlist(symbol) {
  return client.delete(`/api/watchlist/${encodeURIComponent(symbol)}`);
}

export function searchStocks(query) {
  return client.get('/api/watchlist/search', { params: { q: query } });
}
