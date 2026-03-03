import { useContext, useState } from 'react';
import { MessageSquare, Trash2, Wifi, WifiOff } from 'lucide-react';
import { StockContext } from '../../contexts/StockContext';
import { useWebSocket } from '../../hooks/useWebSocket';
import { deleteConversation } from '../../api/chat';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import toast from 'react-hot-toast';

export default function ChatPanel() {
  const { selectedSymbol } = useContext(StockContext);
  const { messages, streaming, activeTool, connected, historyLoading, sendMessage, clearMessages } =
    useWebSocket(selectedSymbol);
  const [confirmClear, setConfirmClear] = useState(false);

  const handleClear = async () => {
    try {
      await deleteConversation(selectedSymbol);
      clearMessages();
      toast.success('Conversation cleared');
    } catch {
      toast.error('Failed to clear conversation');
    }
    setConfirmClear(false);
  };

  if (!selectedSymbol) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <MessageSquare className="h-12 w-12 text-surface-300 dark:text-surface-600 mb-3" />
        <p className="text-sm text-surface-500 dark:text-surface-400">
          Select a stock to start chatting with your AI assistant.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="relative flex items-center justify-center px-4 py-3 border-b border-blue-100 dark:border-surface-700">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          <h3 className="text-sm font-semibold text-surface-900 dark:text-surface-100">
            AI Chat — {selectedSymbol}
          </h3>
        </div>
        <div className="absolute right-4 flex items-center gap-2">
          {connected ? (
            <Wifi className="h-4 w-4 text-positive" />
          ) : (
            <WifiOff className="h-4 w-4 text-surface-400 dark:text-surface-500" />
          )}
          <button
            onClick={() => setConfirmClear(true)}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-blue-100 dark:hover:bg-surface-800 text-surface-400 dark:text-surface-500 hover:text-negative disabled:opacity-30 transition-colors"
            aria-label="Clear conversation"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <ChatMessages
        messages={messages}
        activeTool={activeTool}
        streaming={streaming}
        historyLoading={historyLoading}
      />

      {/* Input */}
      <ChatInput onSend={sendMessage} disabled={!connected || streaming} />

      {/* Confirm clear modal */}
      <Modal
        open={confirmClear}
        onClose={() => setConfirmClear(false)}
        title="Clear conversation"
        actions={
          <>
            <Button variant="ghost" onClick={() => setConfirmClear(false)}>Cancel</Button>
            <Button variant="danger" onClick={handleClear}>Clear</Button>
          </>
        }
      >
        <p className="text-sm">
          This will permanently delete all messages for {selectedSymbol}. This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}
