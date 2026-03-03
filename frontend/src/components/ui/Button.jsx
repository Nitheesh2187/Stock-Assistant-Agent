export default function Button({ children, variant = 'primary', size = 'md', className = '', disabled, ...props }) {
  const base = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 dark:focus:ring-offset-surface-900',
    secondary: 'bg-surface-200 text-surface-700 hover:bg-surface-200/80 dark:bg-surface-700 dark:text-surface-200 dark:hover:bg-surface-700/80 focus:ring-surface-200 dark:focus:ring-offset-surface-900',
    danger: 'bg-negative text-white hover:bg-red-600 focus:ring-red-500 dark:focus:ring-offset-surface-900',
    ghost: 'text-surface-700 hover:bg-surface-100 dark:text-surface-200 dark:hover:bg-surface-800 focus:ring-surface-200 dark:focus:ring-offset-surface-900',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
