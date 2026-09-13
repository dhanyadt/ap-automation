import React from 'react';
import { CreditCard } from 'lucide-react';

export const Payments: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Payment Disbursements & Advice</h1>
        <p className="text-sm text-slate-400">Payment advice generation, UTR settlement tracking, and banking mock rail</p>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-8 text-center max-w-2xl mx-auto shadow-xl">
        <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mx-auto mb-4">
          <CreditCard className="w-7 h-7" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">Phase 3 Payment Rail Integration</h3>
        <p className="text-sm text-slate-400 leading-relaxed">
          The <code className="text-blue-400">Payment</code> model and <code className="text-blue-400">MockPaymentGateway</code> will orchestrate bank payment requests, automated UTR transaction reference generation, and downloadable payment advice in Phase 3.
        </p>
      </div>
    </div>
  );
};
