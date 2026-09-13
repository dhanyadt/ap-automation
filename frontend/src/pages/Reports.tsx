import React from 'react';
import { BarChart3 } from 'lucide-react';

export const Reports: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Financial & Compliance Reports</h1>
        <p className="text-sm text-slate-400">AP Aging buckets, Exception summaries, and GST reconciliation with CSV export</p>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-8 text-center max-w-2xl mx-auto shadow-xl">
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-4">
          <BarChart3 className="w-7 h-7" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">Phase 4 Reporting Engine</h3>
        <p className="text-sm text-slate-400 leading-relaxed">
          AP Aging (0-30, 31-60, 61-90, 90+ days), GST ITC Reconciliation, and Exception exports will be delivered in Phase 4.
        </p>
      </div>
    </div>
  );
};
