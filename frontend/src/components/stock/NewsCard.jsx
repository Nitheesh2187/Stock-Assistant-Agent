import { useContext } from 'react';
import { ExternalLink, Copy } from 'lucide-react';
import { StockContext } from '../../contexts/StockContext';

export default function NewsCard({ article }) {
  const { setChatDraft } = useContext(StockContext);
  const title = article.title || article.headline;
  const summary = article.summary || article.description || article.snippet;
  const url = article.url || article.link;
  const source = article.source || article.publisher;
  const date = article.published_at || article.time_published || article.date;

  const handleCopyToChat = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setChatDraft(url || title);
  };

  return (
    <div className="p-4 bg-white dark:bg-surface-900 rounded-lg border border-surface-200 dark:border-surface-800 hover:border-primary-300 dark:hover:border-primary-700 transition-colors group">
      <div className="flex items-start justify-between gap-2">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 min-w-0"
        >
          <h4 className="text-sm font-semibold text-surface-900 dark:text-surface-100 line-clamp-2 group-hover:text-primary-600">
            {title}
          </h4>
        </a>
        <div className="flex items-center gap-1.5 shrink-0 mt-0.5">
          <button
            onClick={handleCopyToChat}
            className="p-1 rounded hover:bg-surface-100 dark:hover:bg-surface-800 text-surface-400 dark:text-surface-500 hover:text-primary-600 transition-colors"
            title="Copy to chat"
          >
            <Copy className="h-3.5 w-3.5" />
          </button>
          <a href={url} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="h-4 w-4 text-surface-400 dark:text-surface-500" />
          </a>
        </div>
      </div>
      {summary && (
        <p className="text-xs text-surface-600 dark:text-surface-400 mt-1.5 line-clamp-2">{summary}</p>
      )}
      <div className="flex items-center gap-2 mt-2 text-xs text-surface-500 dark:text-surface-400">
        {source && <span>{typeof source === 'object' ? source.name : source}</span>}
        {date && <span>{new Date(date).toLocaleDateString()}</span>}
      </div>
    </div>
  );
}
