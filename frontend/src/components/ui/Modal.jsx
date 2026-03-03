import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

export default function Modal({ open, onClose, title, children, actions }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className="bg-white dark:bg-surface-800 rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-surface-900 dark:text-surface-100">{title}</h3>
          <button onClick={onClose} className="text-surface-400 hover:text-surface-700 dark:text-surface-500 dark:hover:text-surface-200">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="text-surface-600 dark:text-surface-300">{children}</div>
        {actions && <div className="flex justify-end gap-3 mt-6">{actions}</div>}
      </div>
    </div>
  );
}
