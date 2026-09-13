import React, { useEffect, useState } from 'react';
import { ShoppingCart, Search } from 'lucide-react';
import { api } from '../services/api';

export const PurchaseOrders: React.FC = () => {
  const [pos, setPos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPOs = async () => {
      try {
        const res = await api.get('/purchase-orders/');
        setPos(res.data?.results || []);
      } catch (err) {
        console.error('Failed to load purchase orders:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchPOs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Purchase Orders (PO)</h1>
        <p className="text-sm text-slate-400">Manage issued purchase orders and line items for 2-way and 3-way matching</p>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-850/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="p-3.5 pl-5">PO Number</th>
                <th className="p-3.5">Vendor</th>
                <th className="p-3.5">Subtotal</th>
                <th className="p-3.5">Tax Amount</th>
                <th className="p-3.5">Total (INR)</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5 pr-5">Issue Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    Loading purchase orders...
                  </td>
                </tr>
              ) : pos.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No purchase orders found.
                  </td>
                </tr>
              ) : (
                pos.map((po) => (
                  <tr key={po.id} className="hover:bg-slate-750/30 transition-colors">
                    <td className="p-3.5 pl-5 font-mono text-blue-400 font-semibold">{po.po_number}</td>
                    <td className="p-3.5 text-white font-medium">{po.vendor_name}</td>
                    <td className="p-3.5 text-slate-300">₹{parseFloat(po.subtotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className="p-3.5 text-slate-400">₹{parseFloat(po.tax_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className="p-3.5 text-emerald-400 font-semibold">₹{parseFloat(po.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold border bg-purple-500/10 text-purple-400 border-purple-500/20">
                        {po.status}
                      </span>
                    </td>
                    <td className="p-3.5 pr-5 text-slate-400">{po.issue_date}</td>
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
