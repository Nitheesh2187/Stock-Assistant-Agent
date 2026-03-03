import client from './client';

export function register({ email, name, password }) {
  return client.post('/api/auth/register', { email, name, password });
}

export function login({ email, password }) {
  return client.post('/api/auth/login', { email, password });
}

export function refreshToken(refresh_token) {
  return client.post('/api/auth/refresh', { refresh_token });
}

export function getMe() {
  return client.get('/api/auth/me');
}
