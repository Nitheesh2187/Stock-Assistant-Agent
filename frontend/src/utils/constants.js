// In dev, leave empty so requests go through the Vite proxy (no CORS).
// In production, set VITE_API_URL to the backend origin.
export const API_URL = import.meta.env.VITE_API_URL || '';

// WebSocket: use the current host when no explicit API URL is set.
// Automatically picks wss:// on HTTPS pages, ws:// on HTTP.
export const WS_URL = API_URL
  ? API_URL.replace(/^http/, 'ws')
  : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
