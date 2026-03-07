import { useState, useCallback, useEffect } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';

export default function ExpandableBlock({ children, className = '' }) {
  const [expanded, setExpanded] = useState(false);

  const toggle = useCallback(() => setExpanded((v) => !v), []);

  // Close on Escape
  useEffect(() => {
    if (!expanded) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') setExpanded(false);
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [expanded]);

  // Prevent body scroll when expanded
  useEffect(() => {
    if (expanded) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [expanded]);

  // Support render prop: children(expanded) or plain children
  const content = typeof children === 'function' ? children(expanded) : children;

  if (expanded) {
    return (
      <div className="fixed inset-0 z-[100] bg-white dark:bg-surface-950 flex flex-col">
        <div className="flex-shrink-0 flex justify-end p-2 border-b border-surface-200 dark:border-surface-800">
          <button
            onClick={toggle}
            className="p-1.5 rounded-lg hover:bg-surface-200 dark:hover:bg-surface-800 text-surface-500 dark:text-surface-400 transition-colors"
            title="Exit fullscreen (Esc)"
          >
            <Minimize2 size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-auto min-h-0">
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className={`relative group/expand ${className}`}>
      <button
        onClick={toggle}
        className="absolute top-2 right-2 z-20 p-1.5 rounded-lg bg-white/80 dark:bg-surface-800/80 hover:bg-surface-200 dark:hover:bg-surface-700 text-surface-500 dark:text-surface-400 opacity-0 group-hover/expand:opacity-100 transition-opacity shadow-sm"
        title="Expand to fullscreen"
      >
        <Maximize2 size={16} />
      </button>
      {content}
    </div>
  );
}
