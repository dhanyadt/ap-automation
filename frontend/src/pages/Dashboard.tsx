import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight, Building2, CheckCircle2, Clock, FileText, PackageCheck, RefreshCw,
  ShoppingCart, TrendingUp,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';

type Invoice = {
  id: string;
  invoice_date: string | null;
  due_date: string | null;
  total_amount: string;
  vendor_name?: string;
  ocr_confidence: string;
  processing_status: string;
  payment_status: string;
  created_at: string;
  updated_at: string;
};

type Payment = { amount: string; status: string };
type Approval = { invoice_total: string; status: string };

const money = (value: number) => `INR ${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [invoiceCount, setInvoiceCount] = useState(0);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [counts, setCounts] = useState({ vendors: 0, pos: 0, grns: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const [invoiceResponse, paymentResponse, approvalResponse, vendorResponse, poResponse, grnResponse] = await Promise.all([
        api.get('/invoices/?page_size=100'),
        api.get('/payments/?page_size=100'),
        api.get('/approvals/?status=PENDING&page_size=100'),
        api.get('/vendors/'),
        api.get('/purchase-orders/'),
        api.get('/goods-receipts/'),
      ]);
      setInvoices(invoiceResponse.data?.results || []);
      setInvoiceCount(invoiceResponse.data?.count || 0);
      setPayments(paymentResponse.data?.results || []);
      setApprovals(approvalResponse.data?.results || []);
      setCounts({
        vendors: vendorResponse.data?.count || 0,
        pos: poResponse.data?.count || 0,
        grns: grnResponse.data?.count || 0,
      });
    } catch {
      setError('Some dashboard metrics could not be loaded. Please refresh to try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDashboard(); }, []);

  const aging = useMemo(() => {
    const buckets = [0, 0, 0, 0];
    const today = new Date();
    invoices.filter((invoice) => !['PAID', 'CANCELLED'].includes(invoice.payment_status)).forEach((invoice) => {
      const date = invoice.due_date || invoice.invoice_date;
      if (!date) return;
      const days = Math.floor((today.getTime() - new Date(date).getTime()) / 86400000);
      if (days < 0) return;
      buckets[days <= 30 ? 0 : days <= 60 ? 1 : days <= 90 ? 2 : 3] += Number(invoice.total_amount || 0);
    });
    return buckets;
  }, [invoices]);

  const vendorTotals = useMemo(() => {
    const grouped: Record<string, { count: number; value: number }> = {};
    invoices.forEach((invoice) => {
      const name = invoice.vendor_name || 'Unknown vendor';
      grouped[name] = grouped[name] || { count: 0, value: 0 };
      grouped[name].count += 1;
      grouped[name].value += Number(invoice.total_amount || 0);
    });
    return Object.entries(grouped).sort(([, a], [, b]) => b.value - a.value).slice(0, 5);
  }, [invoices]);

  const pendingApprovalValue = approvals.filter((item) => item.status === 'PENDING')
    .reduce((sum, item) => sum + Number(item.invoice_total || 0), 0);
  const requestedPayments = payments.filter((payment) => payment.status === 'REQUESTED');
  const paidPayments = payments.filter((payment) => payment.status === 'PAID');
  const ocrInvoices = invoices.filter((invoice) => Number(invoice.ocr_confidence) > 0);
  const ocrAccuracy = ocrInvoices.length
    ? ocrInvoices.reduce((sum, invoice) => sum + Number(invoice.ocr_confidence), 0) / ocrInvoices.length
    : null;
  const completedInvoices = invoices.filter((invoice) => ['APPROVED', 'PAID'].includes(invoice.processing_status));
  const turnaround = completedInvoices.length
    ? completedInvoices.reduce((sum, invoice) => sum + (new Date(invoice.updated_at).getTime() - new Date(invoice.created_at).getTime()), 0) / completedInvoices.length / 86400000
    : null;

  const stats = [
    { label: 'Active Invoices', value: invoiceCount, icon: FileText, path: '/invoices' },
    { label: 'Registered Vendors', value: counts.vendors, icon: Building2, path: '/vendors' },
    { label: 'Purchase Orders', value: counts.pos, icon: ShoppingCart, path: '/purchase-orders' },
    { label: 'Goods Receipts (GRN)', value: counts.grns, icon: PackageCheck, path: '/goods-receipts' },
  ];
  const agingLabels = ['0–30 days', '31–60 days', '61–90 days', '90+ days'];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-2xl border border-slate-700/60 bg-gradient-to-r from-blue-900/40 via-slate-800 to-indigo-900/30 p-6 shadow-xl md:flex-row md:items-center md:justify-between">
        <div>
          <span className="rounded-full border border-blue-500/20 bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-400">AP OPERATIONS OVERVIEW</span>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-white">Welcome back, {user?.first_name || user?.email}!</h1>
          <p className="mt-1 text-sm text-slate-400">Logged in as <span className="font-semibold text-slate-200">{user?.role}</span> in <span className="font-semibold text-slate-200">{user?.department || 'Operations'}</span></p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={fetchDashboard} className="inline-flex items-center gap-2 rounded-xl border border-slate-600 px-3 py-2.5 text-sm text-slate-300 hover:bg-slate-700"><RefreshCw className="h-4 w-4" /> Refresh</button>
          <Link to="/invoices" className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-500">Manage Invoices <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </div>
      {error && <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300">{error}</div>}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => { const Icon = stat.icon; return <Link key={stat.label} to={stat.path} className="group rounded-2xl border border-slate-700/60 bg-slate-800/80 p-5 hover:bg-slate-800"><div className="flex items-center justify-between"><span className="text-xs font-medium text-slate-400">{stat.label}</span><Icon className="h-4 w-4 text-slate-300" /></div><div className="mt-3 text-2xl font-bold text-white">{loading ? '...' : stat.value}</div><div className="mt-2 flex items-center text-[11px] text-slate-400 group-hover:text-blue-400">View records <ArrowRight className="ml-1 h-3 w-3" /></div></Link>; })}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-2xl border border-slate-700/60 bg-slate-800/80 p-5 lg:col-span-2">
          <div className="flex items-center justify-between"><div><h2 className="font-semibold text-white">Invoice aging</h2><p className="mt-1 text-xs text-slate-500">Outstanding invoice value by due date</p></div><Clock className="h-5 w-5 text-amber-400" /></div>
          <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">{agingLabels.map((label, index) => <div key={label} className="rounded-lg bg-slate-900/50 p-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-2 text-sm font-semibold text-white">{loading ? '...' : money(aging[index])}</p></div>)}</div>
        </section>
        <section className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5"><h2 className="font-semibold text-white">Pending approvals</h2><p className="mt-1 text-xs text-slate-500">Requests routed to approval roles</p><p className="mt-5 text-3xl font-bold text-amber-300">{loading ? '...' : approvals.length}</p><p className="mt-1 text-sm text-amber-200/80">{money(pendingApprovalValue)} awaiting decision</p><Link to="/approvals" className="mt-4 inline-flex items-center text-xs font-medium text-amber-300 hover:text-amber-200">Open queue <ArrowRight className="ml-1 h-3 w-3" /></Link></section>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-2xl border border-slate-700/60 bg-slate-800/80 p-5"><div className="flex items-center justify-between"><h2 className="font-semibold text-white">Processing health</h2><TrendingUp className="h-5 w-5 text-blue-400" /></div><div className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-lg bg-slate-900/50 p-3"><p className="text-xs text-slate-500">OCR accuracy</p><p className="mt-2 text-xl font-bold text-cyan-300">{ocrAccuracy === null ? 'N/A' : `${ocrAccuracy.toFixed(1)}%`}</p></div><div className="rounded-lg bg-slate-900/50 p-3"><p className="text-xs text-slate-500">Avg turnaround</p><p className="mt-2 text-xl font-bold text-white">{turnaround === null ? 'N/A' : `${turnaround.toFixed(1)}d`}</p></div></div><p className="mt-3 text-[11px] text-slate-500">Derived only from recorded OCR confidence and invoice timestamps.</p></section>
        <section className="rounded-2xl border border-slate-700/60 bg-slate-800/80 p-5"><h2 className="font-semibold text-white">Payment tracking</h2><p className="mt-1 text-xs text-slate-500">Current payment rail totals</p><div className="mt-5 space-y-3"><div className="flex justify-between text-sm"><span className="text-slate-400">Requested ({requestedPayments.length})</span><span className="font-semibold text-amber-300">{money(requestedPayments.reduce((s, p) => s + Number(p.amount), 0))}</span></div><div className="flex justify-between text-sm"><span className="text-slate-400">Settled ({paidPayments.length})</span><span className="font-semibold text-emerald-300">{money(paidPayments.reduce((s, p) => s + Number(p.amount), 0))}</span></div></div><Link to="/payments" className="mt-4 inline-flex items-center text-xs font-medium text-blue-300">View payments <ArrowRight className="ml-1 h-3 w-3" /></Link></section>
        <section className="rounded-2xl border border-slate-700/60 bg-slate-800/80 p-5"><h2 className="font-semibold text-white">Vendor-wise analytics</h2><p className="mt-1 text-xs text-slate-500">Top vendors by invoice value</p><div className="mt-4 space-y-3">{vendorTotals.length ? vendorTotals.map(([name, data]) => <div key={name} className="flex items-center justify-between gap-3"><div className="min-w-0"><p className="truncate text-sm text-slate-300">{name}</p><p className="text-[11px] text-slate-500">{data.count} invoice{data.count === 1 ? '' : 's'}</p></div><span className="whitespace-nowrap text-sm font-semibold text-white">{money(data.value)}</span></div>) : <p className="text-sm text-slate-500">No vendor invoice data.</p>}</div></section>
      </div>
      <div className="rounded-2xl border border-slate-700/50 bg-slate-800/50 p-5"><h3 className="flex items-center text-sm font-semibold text-white"><CheckCircle2 className="mr-2 h-4 w-4 text-emerald-400" /> Workflow connected</h3><p className="mt-2 text-xs leading-relaxed text-slate-400">Live KPIs are derived from the existing invoice, approval, payment, vendor, PO, and GRN APIs. No synthetic dashboard records are used.</p></div>
    </div>
  );
};
