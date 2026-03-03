export default function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      {Icon && <Icon className="h-16 w-16 text-surface-300 dark:text-surface-600 mb-4" />}
      <h3 className="text-lg font-medium text-surface-900 dark:text-surface-100 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-surface-500 dark:text-surface-400 max-w-sm">{description}</p>
      )}
    </div>
  );
}
