import axios from 'axios';
import { API_URL } from '../utils/constants';

const client = axios.create({
  baseURL: API_URL,
});

/**
 * Lazy-create a session via POST /api/session and cache in sessionStorage.
 * Each browser tab gets its own isolated session.
 */
let sessionPromise = null;

export function getSessionId() {
  return sessionStorage.getItem('session_id');
}

async function ensureSession() {
  const existing = getSessionId();
  if (existing) return existing;

  // Deduplicate concurrent calls
  if (!sessionPromise) {
    sessionPromise = axios
      .post(`${API_URL}/api/session`)
      .then(({ data }) => {
        sessionStorage.setItem('session_id', data.session_id);
        return data.session_id;
      })
      .finally(() => {
        sessionPromise = null;
      });
  }
  return sessionPromise;
}

// Attach X-Session-Id header to every request
client.interceptors.request.use(async (config) => {
  const sessionId = await ensureSession();
  config.headers['X-Session-Id'] = sessionId;
  return config;
});

export default client;
