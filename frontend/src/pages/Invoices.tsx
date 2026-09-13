import React, { useEffect, useState } from 'react';
import { FileText, Upload, Filter, Search, Plus, Calendar, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export const Invoices: React.FC = () => {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/invoices/?search=${searchTerm}`);
      setInvoices(res.data?.results || []);
    } catch (err) {
      console.error('Failed to load invoices:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [searchTerm]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'UPLOADED':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'APPROVED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'PAID':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'EXCEPTION':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Invoice Ingestion & Management</h1>
          <p className="text-sm text-slate-400">Capture, track, and monitor invoice documents across stages</p>
        </div>
      </div>

      {/* Search & Filter bar */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by invoice #, vendor, PO number..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <span className="text-xs text-slate-400">{invoices.length} invoices found</span>
      </div>

      {/* Table */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-850/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="p-3.5 pl-5">Invoice #</th>
                <th className="p-3.5">Vendor</th>
                <th className="p-3.5">Fiscal Year</th>
                <th className="p-3.5">Total Amount</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">OCR / Confidence</th>
                <th className="p-3.5 pr-5">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    Loading invoices...
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No invoices registered yet. Upload an invoice via POST /api/v1/invoices/upload/ or using API.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-750/30 transition-colors">
                    <td className="p-3.5 pl-5 font-semibold text-white">
                      {inv.invoice_number || inv.original_filename || 'Pending OCR'}
                    </td>
                    <td className="p-3.5 text-slate-300">{inv.vendor_name || 'Unassigned'}</td>
                    <td className="p-3.5 text-slate-400">{inv.fiscal_year}</td>
                    <td className="p-3.5 font-medium text-emerald-400">
                      ₹{parseFloat(inv.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-3.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${getStatusBadge(inv.processing_status)}`}>
                        {inv.processing_status}
                      </span>
                    </td>
                    <td className="p-3.5 text-slate-400">
                      {inv.ocr_status} ({inv.ocr_confidence}%)
                    </td>
                    <td className="p-3.5 pr-5 text-slate-400">
                      {inv.invoice_date || new Date(inv.created_at).toLocaleDateString()}
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
