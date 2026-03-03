export default function Avatar({ name, size = 'md', className = '' }) {
  const initials = (name || '?')
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  const sizes = {
    sm: 'h-7 w-7 text-xs',
    md: 'h-9 w-9 text-sm',
    lg: 'h-11 w-11 text-base',
  };

  return (
    <div
      className={`inline-flex items-center justify-center rounded-full bg-blue-800 text-white font-semibold ${sizes[size]} ${className}`}
    >
      {initials}
    </div>
  );
}
