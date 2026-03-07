import { useState, useEffect, useRef, useCallback } from 'react';
import { getMessages } from '../api/chat';
import { WS_URL } from '../utils/constants';
import { getSessionId } from '../api/client';

export function useWebSocket(symbol) {
  const [messages, setMessages] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [activeTool, setActiveTool] = useState(null);
  const [connected, setConnected] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const wsRef = useRef(null);
  const streamBufferRef = useRef('');

  // Load message history
  useEffect(() => {
    if (!symbol) {
      setMessages([]);
      return;
    }

    let cancelled = false;
    setHistoryLoading(true);

    getMessages(symbol, { limit: 100 })
      .then(({ data }) => {
        if (!cancelled) {
          setMessages(data.messages || []);
        }
      })
      .catch(() => {
        if (!cancelled) setMessages([]);
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false);
      });

    return () => { cancelled = true; };
  }, [symbol]);

  // WebSocket connection
  useEffect(() => {
    if (!symbol) return;

    const sessionId = getSessionId();
    if (!sessionId) return;

    const ws = new WebSocket(
      `${WS_URL}/api/chat/${encodeURIComponent(symbol)}/ws?session_id=${encodeURIComponent(sessionId)}`
    );
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'token':
          streamBufferRef.current += data.content;
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === 'assistant' && last._streaming) {
              return [
                ...prev.slice(0, -1),
                { ...last, content: streamBufferRef.current },
              ];
            }
            return [
              ...prev,
              { role: 'assistant', content: streamBufferRef.current, _streaming: true },
            ];
          });
          break;

        case 'tool_start':
          setActiveTool(data.tool_name);
          break;

        case 'tool_end':
          setActiveTool(null);
          break;

        case 'done':
          setStreaming(false);
          setActiveTool(null);
          streamBufferRef.current = '';
          // Finalize the streaming message
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?._streaming) {
              const { _streaming, ...rest } = last;
              return [...prev.slice(0, -1), rest];
            }
            return prev;
          });
          break;

        case 'error':
          setStreaming(false);
          setActiveTool(null);
          streamBufferRef.current = '';
          setMessages((prev) => [
            ...prev,
            { role: 'error', content: data.content },
          ]);
          break;
      }
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    return () => {
      ws.close();
      wsRef.current = null;
      setConnected(false);
      setStreaming(false);
      setActiveTool(null);
      streamBufferRef.current = '';
    };
  }, [symbol]);

  const sendMessage = useCallback((content) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    // Add optimistic user message
    setMessages((prev) => [...prev, { role: 'user', content }]);
    setStreaming(true);
    streamBufferRef.current = '';

    wsRef.current.send(JSON.stringify({ type: 'message', content }));
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    streaming,
    activeTool,
    connected,
    historyLoading,
    sendMessage,
    clearMessages,
  };
}
