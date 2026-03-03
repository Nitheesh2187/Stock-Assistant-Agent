import { useState } from 'react';
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from 'lucide-react';
import { useResizable } from '../../hooks/useResizable';

export default function DashboardLayout({ sidebar, center, chat }) {
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  const leftResize = useResizable({
    direction: 'horizontal',
    initialSize: 280,
    minSize: 200,
    maxSize: 420,
    storageKey: 'sidebar-width',
  });

  const rightResize = useResizable({
    direction: 'horizontal',
    initialSize: 360,
    minSize: 280,
    maxSize: 500,
    storageKey: 'chat-width',
    invertDelta: true,
  });

  const anyDragging = leftResize.isDragging || rightResize.isDragging;

  return (
    <div className="h-screen flex overflow-hidden bg-surface-100 dark:bg-surface-950">
      {anyDragging && <div className="fixed inset-0 z-50" />}

      {/* Left sidebar — full height */}
      {leftCollapsed ? (
        <div className="flex-shrink-0 flex items-start border-r border-blue-100 dark:border-surface-700 bg-blue-50 dark:bg-surface-900">
          <button
            onClick={() => setLeftCollapsed(false)}
            className="p-2 hover:bg-blue-100 dark:hover:bg-surface-800 text-surface-500 dark:text-surface-400 transition-colors"
            title="Show watchlist"
          >
            <PanelLeftOpen size={16} />
          </button>
        </div>
      ) : (
        <aside
          className="relative flex-shrink-0 flex flex-col border-r border-blue-100 dark:border-surface-700 bg-blue-50 dark:bg-surface-900"
          style={{ width: leftResize.size }}
        >
          <button
            onClick={() => setLeftCollapsed(true)}
            className="absolute top-2.5 right-2 z-20 p-1 rounded hover:bg-blue-100 dark:hover:bg-surface-800 text-surface-400 dark:text-surface-500 transition-colors"
            title="Hide watchlist"
          >
            <PanelLeftClose size={14} />
          </button>
          <div className="flex-1 flex flex-col overflow-hidden">
            {sidebar}
          </div>
          <div
            onMouseDown={leftResize.handleMouseDown}
            className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary-500/40 active:bg-primary-500/60 transition-colors z-10"
          />
        </aside>
      )}

      {/* Center */}
      <main className="flex-1 overflow-hidden min-w-0">
        {center}
      </main>

      {/* Right chat panel — full height */}
      {rightCollapsed ? (
        <div className="flex-shrink-0 flex items-start border-l border-blue-100 dark:border-surface-700 bg-blue-50 dark:bg-surface-900">
          <button
            onClick={() => setRightCollapsed(false)}
            className="p-2 hover:bg-blue-100 dark:hover:bg-surface-800 text-surface-500 dark:text-surface-400 transition-colors"
            title="Show chat"
          >
            <PanelRightOpen size={16} />
          </button>
        </div>
      ) : (
        <aside
          className="relative flex-shrink-0 flex flex-col border-l border-blue-100 dark:border-surface-700 bg-blue-50 dark:bg-surface-900 overflow-hidden"
          style={{ width: rightResize.size }}
        >
          <button
            onClick={() => setRightCollapsed(true)}
            className="absolute top-2.5 left-2 z-20 p-1 rounded hover:bg-blue-100 dark:hover:bg-surface-800 text-surface-400 dark:text-surface-500 transition-colors"
            title="Hide chat"
          >
            <PanelRightClose size={14} />
          </button>
          <div
            onMouseDown={rightResize.handleMouseDown}
            className="absolute top-0 left-0 w-1 h-full cursor-col-resize hover:bg-primary-500/40 active:bg-primary-500/60 transition-colors z-10"
          />
          {chat}
        </aside>
      )}
    </div>
  );
}
