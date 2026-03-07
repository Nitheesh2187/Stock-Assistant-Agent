const CRORE = 1e7;

function formatValue(v, inCrores) {
  if (v === null || v === undefined || v === 'None') return '-';
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  if (typeof v === 'number') {
    if (!Number.isFinite(v)) return '-';
    if (inCrores) {
      return (v / CRORE).toLocaleString('en-IN', { maximumFractionDigits: 2 });
    }
    if (Number.isInteger(v)) return v.toLocaleString('en-IN');
    return v.toFixed(2);
  }
  return String(v);
}

/**
 * Check if a column of values has any value >= 1 Cr, meaning the column
 * should be displayed in crores.
 */
function columnHasCrores(data, dates, metric) {
  return dates.some((d) => {
    const v = data[d]?.[metric];
    return typeof v === 'number' && Number.isFinite(v) && Math.abs(v) >= CRORE;
  });
}

function formatDateCol(dateStr) {
  try {
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString('en-IN', { year: 'numeric', month: 'short' });
  } catch {
    return dateStr;
  }
}

function formatLabel(key) {
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/_/g, ' ')
    .replace(/^./, (s) => s.toUpperCase())
    .trim();
}

/**
 * Detect if data is a "pivot" shape: { date1: { metric: val }, date2: { metric: val } }
 */
function isPivotData(data) {
  const vals = Object.values(data);
  return (
    vals.length > 0 &&
    vals.every((v) => typeof v === 'object' && v !== null && !Array.isArray(v))
  );
}

/**
 * Render a pivot table: metrics as rows, date columns.
 */
function PivotTable({ data }) {
  const dates = Object.keys(data);
  // Collect all metric keys preserving first-seen order
  const metricSet = new Set();
  dates.forEach((d) => Object.keys(data[d]).forEach((k) => metricSet.add(k)));
  const metrics = [...metricSet];

  // Pre-compute which metrics should display in crores
  const croreFlags = {};
  metrics.forEach((m) => {
    croreFlags[m] = columnHasCrores(data, dates, m);
  });

  // Check if any metric uses crores (to show hint in header)
  const anyCrores = Object.values(croreFlags).some(Boolean);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-white dark:bg-surface-900 z-10">
          <tr className="border-b border-surface-200 dark:border-surface-700">
            <th className="py-2 px-3 text-left text-surface-500 dark:text-surface-400 font-semibold">Metric</th>
            {dates.map((d) => (
              <th key={d} className="py-2 px-3 text-right text-surface-500 dark:text-surface-400 font-semibold whitespace-nowrap">
                <div>{formatDateCol(d)}</div>
                {anyCrores && (
                  <div className="text-[10px] font-normal text-surface-400 dark:text-surface-500">
                    ({'\u20B9'} in Cr)
                  </div>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => (
            <tr key={metric} className="border-b border-surface-100 dark:border-surface-800 last:border-0 even:bg-surface-50 dark:even:bg-surface-800/50">
              <td className="py-2 px-3 text-surface-600 dark:text-surface-400 font-medium whitespace-nowrap">
                {formatLabel(metric)}
              </td>
              {dates.map((d) => (
                <td key={d} className="py-2 px-3 text-right text-surface-900 dark:text-surface-100 font-mono whitespace-nowrap">
                  {formatValue(data[d]?.[metric], croreFlags[metric])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Render a flat key-value table.
 */
function FlatTable({ entries }) {
  const anyCrores = entries.some(
    ([, v]) => typeof v === 'number' && Number.isFinite(v) && Math.abs(v) >= CRORE
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        {anyCrores && (
          <thead className="sticky top-0 bg-white dark:bg-surface-900 z-10">
            <tr className="border-b border-surface-200 dark:border-surface-700">
              <th className="py-2 px-3 text-left text-surface-500 dark:text-surface-400 font-semibold">Field</th>
              <th className="py-2 px-3 text-right text-surface-500 dark:text-surface-400 font-semibold">
                <div>Value</div>
                <div className="text-[10px] font-normal text-surface-400 dark:text-surface-500">
                  ({'\u20B9'} in Cr where applicable)
                </div>
              </th>
            </tr>
          </thead>
        )}
        <tbody>
          {entries.map(([key, value]) => {
            const isCr = typeof value === 'number' && Number.isFinite(value) && Math.abs(value) >= CRORE;
            return (
              <tr key={key} className="border-b border-surface-100 dark:border-surface-800 last:border-0 even:bg-surface-50 dark:even:bg-surface-800/50">
                <td className="py-2 px-3 text-surface-600 dark:text-surface-400 font-medium whitespace-nowrap">
                  {formatLabel(key)}
                </td>
                <td className="py-2 px-3 text-right text-surface-900 dark:text-surface-100 font-mono">
                  {formatValue(value, isCr)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function FinancialTable({ data }) {
  if (!data || typeof data !== 'object') return null;

  // Pivot table for {date: {metric: value}} shape (financials, balance_sheet, cashflow)
  if (isPivotData(data)) {
    return <PivotTable data={data} />;
  }

  // Flat key-value table for info / overview
  const entries = Object.entries(data).filter(
    ([, val]) => val !== null && val !== undefined && val !== 'None' && val !== '-'
  );

  if (entries.length === 0) {
    return <p className="text-sm text-surface-500 dark:text-surface-400 p-4">No data available.</p>;
  }

  return <FlatTable entries={entries} />;
}
