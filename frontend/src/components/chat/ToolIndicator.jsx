import { Wrench } from 'lucide-react';
import Spinner from '../ui/Spinner';

export default function ToolIndicator({ toolName }) {
  if (!toolName) return null;

  const label = toolName
    .replace(/_/g, ' ')
    .replace(/^./, (s) => s.toUpperCase());

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 mx-4 my-1 bg-primary-50 dark:bg-primary-900/20 rounded-lg w-fit">
      <Spinner size="sm" />
      <Wrench className="h-3.5 w-3.5 text-primary-600 dark:text-primary-400" />
      <span className="text-xs font-medium text-primary-700 dark:text-primary-400">
        Using {label}...
      </span>
    </div>
  );
}
