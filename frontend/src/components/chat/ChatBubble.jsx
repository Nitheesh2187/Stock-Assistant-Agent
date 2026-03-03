import ReactMarkdown from 'react-markdown';
import { Bot, User, AlertCircle } from 'lucide-react';

export default function ChatBubble({ message }) {
  const { role, content } = message;

  if (role === 'error') {
    return (
      <div className="flex gap-2 px-4 py-2">
        <AlertCircle className="h-5 w-5 text-negative shrink-0 mt-0.5" />
        <p className="text-sm text-negative">{content}</p>
      </div>
    );
  }

  const isUser = role === 'user';

  return (
    <div className={`flex gap-2.5 px-4 py-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`shrink-0 h-7 w-7 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary-600 dark:bg-primary-600' : 'bg-surface-200 dark:bg-surface-700'
      }`}>
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-surface-600 dark:text-surface-300" />
        )}
      </div>
      <div className={`max-w-[80%] rounded-xl px-3 py-2 overflow-hidden ${
        isUser
          ? 'bg-blue-100 text-surface-900 dark:bg-primary-600 dark:text-white'
          : 'bg-white dark:bg-surface-800 text-surface-900 dark:text-surface-100'
      }`}>
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
        ) : (
          <div className="text-sm prose prose-sm dark:prose-invert max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 break-words [overflow-wrap:anywhere] [&_a]:break-all">
            <ReactMarkdown>{content || ''}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
