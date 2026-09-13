import React, { useEffect, useState } from 'react';
import { PackageCheck } from 'lucide-react';
import { api } from '../services/api';

export const GoodsReceipts: React.FC = () => {
  const [grns, setGrns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGRNs = async () => {
      try {
        const res = await api.get('/goods-receipts/');
        setGrns(res.data?.results || []);
      } catch (err) {
        console.error('Failed to load GRNs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchGRNs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Goods Receipt Notes (GRN)</h1>
        <p className="text-sm text-slate-400">Warehouse deliveries and inspection receipts required for 3-way matching</p>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-850/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="p-3.5 pl-5">GRN Number</th>
                <th className="p-3.5">PO Reference</th>
                <th className="p-3.5">Vendor</th>
                <th className="p-3.5">Challan #</th>
                <th className="p-3.5">Received By</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5 pr-5">Received Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    Loading goods receipts...
                  </td>
                </tr>
              ) : grns.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No goods receipts recorded yet.
                  </td>
                </tr>
              ) : (
                grns.map((g) => (
                  <tr key={g.id} className="hover:bg-slate-750/30 transition-colors">
                    <td className="p-3.5 pl-5 font-mono text-emerald-400 font-semibold">{g.grn_number}</td>
                    <td className="p-3.5 text-blue-400 font-mono">{g.po_number}</td>
                    <td className="p-3.5 text-white font-medium">{g.vendor_name}</td>
                    <td className="p-3.5 text-slate-400">{g.delivery_challan_number || '—'}</td>
                    <td className="p-3.5 text-slate-300">{g.received_by || 'Store'}</td>
                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                        {g.status}
                      </span>
                    </td>
                    <td className="p-3.5 pr-5 text-slate-400">{g.received_date}</td>
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
