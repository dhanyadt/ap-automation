import React from 'react';
import { CheckSquare, ShieldCheck, Clock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const Approvals: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Approval Queue & Workflow</h1>
        <p className="text-sm text-slate-400">Multi-tier role based approvals with amount-based threshold matrix</p>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-8 text-center max-w-2xl mx-auto shadow-xl">
        <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto mb-4">
          <Clock className="w-7 h-7" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">Phase 3 Workflow Engine Integration</h3>
        <p className="text-sm text-slate-400 leading-relaxed mb-6">
          The database models (<code className="text-blue-400">ApprovalMatrixRule</code>, <code className="text-blue-400">ApprovalRequest</code>, and <code className="text-blue-400">ApprovalAction</code>) are migrated. The interactive mobile-responsive approval workbench will be activated in Phase 3.
        </p>
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-300 text-left">
          <p className="font-semibold text-slate-200 mb-1">Your Eligible Approver Role:</p>
          <p>
            Current account is registered as <strong className="text-amber-400">{user?.role}</strong>. In Phase 3, invoices routed to this role will appear here for one-click approval or escalation.
          </p>
        </div>
      </div>
    </div>
  );
};
