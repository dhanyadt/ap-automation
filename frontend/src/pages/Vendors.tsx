import React, { useEffect, useState } from 'react';
import { Building2, Search, CheckCircle2, XCircle } from 'lucide-react';
import { api } from '../services/api';

export const Vendors: React.FC = () => {
  const [vendors, setVendors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchVendors = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/vendors/?search=${searchTerm}`);
      setVendors(res.data?.results || []);
    } catch (err) {
      console.error('Failed to load vendors:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, [searchTerm]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Vendor Master Directory</h1>
          <p className="text-sm text-slate-400">Manage registered vendor partners, GSTIN compliance, and masked bank rails</p>
        </div>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search vendors by name, code, GSTIN, city..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <span className="text-xs text-slate-400">{vendors.length} vendors active</span>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-850/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="p-3.5 pl-5">Vendor Code</th>
                <th className="p-3.5">Company Name</th>
                <th className="p-3.5">GSTIN / PAN</th>
                <th className="p-3.5">Location</th>
                <th className="p-3.5">Bank Account (Masked)</th>
                <th className="p-3.5">Credit Terms</th>
                <th className="p-3.5 pr-5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    Loading vendors...
                  </td>
                </tr>
              ) : vendors.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No vendors registered yet.
                  </td>
                </tr>
              ) : (
                vendors.map((v) => {
                  const primaryBank = v.bank_accounts?.find((b: any) => b.is_primary) || v.bank_accounts?.[0];
                  return (
                    <tr key={v.id} className="hover:bg-slate-750/30 transition-colors">
                      <td className="p-3.5 pl-5 font-mono text-blue-400 font-semibold">{v.code}</td>
                      <td className="p-3.5 font-medium text-white">{v.name}</td>
                      <td className="p-3.5 font-mono text-slate-300">
                        <div>{v.gstin || '—'}</div>
                        <div className="text-[10px] text-slate-500">{v.pan || ''}</div>
                      </td>
                      <td className="p-3.5 text-slate-400">
                        {v.city ? `${v.city}, ${v.state}` : '—'}
                      </td>
                      <td className="p-3.5">
                        {primaryBank ? (
                          <div>
                            <span className="font-mono text-slate-200">{primaryBank.masked_account_number}</span>
                            <span className="text-[10px] text-slate-400 block">{primaryBank.bank_name}</span>
                          </div>
                        ) : (
                          <span className="text-slate-500 italic">No bank recorded</span>
                        )}
                      </td>
                      <td className="p-3.5 text-slate-300">{v.payment_terms_days} days</td>
                      <td className="p-3.5 pr-5">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            v.status === 'ACTIVE'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          }`}
                        >
                          {v.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
