import { useEffect, useRef } from 'react';
import ChatBubble from './ChatBubble';
import ToolIndicator from './ToolIndicator';
import Spinner from '../ui/Spinner';

export default function ChatMessages({ messages, activeTool, streaming, historyLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTool]);

  if (historyLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto py-3 space-y-1">
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full text-sm text-surface-500 dark:text-surface-400">
          Ask a question about this stock.
        </div>
      )}
      {messages.map((msg, i) => (
        <ChatBubble key={msg.id || i} message={msg} />
      ))}
      {activeTool && <ToolIndicator toolName={activeTool} />}
      <div ref={bottomRef} />
    </div>
  );
}
