export default function FinancialTable({ data }) {
  if (!data || typeof data !== 'object') return null;

  const entries = Object.entries(data).filter(
    ([, val]) => val !== null && val !== undefined && val !== 'None' && val !== '-'
  );

  if (entries.length === 0) {
    return <p className="text-sm text-surface-500 dark:text-surface-400 p-4">No data available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key} className="border-b border-surface-100 dark:border-surface-800 last:border-0 even:bg-surface-50 dark:even:bg-surface-800/50">
              <td className="py-2 px-3 text-surface-600 dark:text-surface-400 font-medium whitespace-nowrap">
                {key.replace(/([A-Z])/g, ' $1').replace(/^./, (s) => s.toUpperCase())}
              </td>
              <td className="py-2 px-3 text-right text-surface-900 dark:text-surface-100 font-mono">
                {String(value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
