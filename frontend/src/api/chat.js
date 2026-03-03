import client from './client';

export function getMessages(symbol, { limit = 50, before } = {}) {
  const params = { limit };
  if (before) params.before = before;
  return client.get(`/api/chat/${encodeURIComponent(symbol)}/messages`, { params });
}

export function deleteConversation(symbol) {
  return client.delete(`/api/chat/${encodeURIComponent(symbol)}`);
}
