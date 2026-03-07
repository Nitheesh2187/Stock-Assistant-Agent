import { useState } from 'react';
import FinancialTable from './FinancialTable';
import ExpandableBlock from '../ui/ExpandableBlock';

export default function FinancialTabs({ fundamentals }) {
  const [activeTab, setActiveTab] = useState('overview');

  if (!fundamentals || typeof fundamentals !== 'object') return null;

  // Flatten if wrapped in a single top-level key (e.g. { result: {...} })
  let data = fundamentals;
  const keys = Object.keys(data);
  if (keys.length === 1 && typeof data[keys[0]] === 'object' && data[keys[0]] !== null) {
    data = data[keys[0]];
  }

  const tabs = [];

  if (typeof data === 'object' && !Array.isArray(data)) {
    const hasNested = Object.values(data).some(
      (v) => typeof v === 'object' && v !== null && !Array.isArray(v)
    );

    if (hasNested) {
      // Collect flat values as overview
      const flat = {};
      Object.entries(data).forEach(([key, val]) => {
        if (typeof val !== 'object' || val === null) flat[key] = val;
      });
      if (Object.keys(flat).length > 0) {
        tabs.push({ id: 'overview', label: 'Overview', data: flat });
      }
      // Collect nested sections as tabs (skip sustainability)
      Object.entries(data).forEach(([key, val]) => {
        if (key === 'sustainability') return;
        if (typeof val === 'object' && val !== null && !Array.isArray(val) && Object.keys(val).length > 0) {
          tabs.push({
            id: key,
            label: key.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').replace(/^./, (s) => s.toUpperCase()),
            data: val,
          });
        }
      });
    } else {
      tabs.push({ id: 'overview', label: 'Overview', data });
    }
  }

  if (tabs.length === 0) return null;

  const activeTabData = tabs.find((t) => t.id === activeTab) || tabs[0];

  return (
    <ExpandableBlock>
      <div className="h-full flex flex-col bg-white dark:bg-surface-900 rounded-lg border border-surface-200 dark:border-surface-800">
        <div className="flex-shrink-0 flex border-b border-surface-200 dark:border-surface-800 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors ${
                (activeTab === tab.id || (!tabs.find((t) => t.id === activeTab) && tab === tabs[0]))
                  ? 'text-primary-600 border-b-2 border-primary-600'
                  : 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-auto min-h-0">
          <FinancialTable data={activeTabData.data} />
        </div>
      </div>
    </ExpandableBlock>
  );
}
