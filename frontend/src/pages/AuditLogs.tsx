import React, { useEffect, useState } from 'react';
import { History, Search } from 'lucide-react';
import { api } from '../services/api';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await api.get('/audit-logs/');
        setLogs(res.data?.results || []);
      } catch (err) {
        console.error('Failed to load audit logs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Append-Only Audit Trail</h1>
        <p className="text-sm text-slate-400">Immutable compliance log recording all system mutations, actors, and IP addresses</p>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-850/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="p-3.5 pl-5">Timestamp</th>
                <th className="p-3.5">Actor</th>
                <th className="p-3.5">Action</th>
                <th className="p-3.5">Entity Type</th>
                <th className="p-3.5">Entity ID</th>
                <th className="p-3.5 pr-5">Changes / Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500">
                    Loading audit trail...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500">
                    No audit records registered yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-750/30 transition-colors">
                    <td className="p-3.5 pl-5 font-mono text-slate-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="p-3.5 text-white font-medium">{log.actor_email}</td>
                    <td className="p-3.5">
                      <span className="font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 font-semibold">
                        {log.action}
                      </span>
                    </td>
                    <td className="p-3.5 font-semibold text-slate-300">{log.entity_type}</td>
                    <td className="p-3.5 font-mono text-slate-400 text-[11px] truncate max-w-[140px]">{log.entity_id}</td>
                    <td className="p-3.5 pr-5 font-mono text-[11px] text-slate-400 truncate max-w-[200px]">
                      {JSON.stringify(log.changes)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
