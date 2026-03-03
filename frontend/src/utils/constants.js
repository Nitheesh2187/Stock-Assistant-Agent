// In dev, leave empty so requests go through the Vite proxy (no CORS).
// In production, set VITE_API_URL to the backend origin.
export const API_URL = import.meta.env.VITE_API_URL || '';

// WebSocket: use the current host when proxied, or the explicit backend URL.
export const WS_URL = API_URL
  ? API_URL.replace(/^http/, 'ws')
  : `ws://${window.location.host}`;
