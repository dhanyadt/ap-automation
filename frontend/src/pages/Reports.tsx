import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, BarChart3, CheckCircle2, Download, RefreshCw, X } from 'lucide-react';
import { api } from '../services/api';

type ValidationResult = {
  rule_code: string;
  severity: string;
  message: string;
};

type Invoice = {
  id: string;
  invoice_number: string;
  vendor_name?: string;
  vendor_gstin_extracted?: string;
  invoice_date: string | null;
  due_date: string | null;
  subtotal: string;
  tax_amount: string;
  total_amount: string;
  currency: string;
  processing_status: string;
  validation_status: string;
  matching_status: string;
  approval_status: string;
  payment_status: string;
  validation_results?: ValidationResult[];
};

type Payment = {
  invoice: string;
  amount: string;
  status: string;
};

type AgingBucket = {
  label: string;
  count: number;
  amount: number;
};

const formatMoney = (amount: number, currency = 'INR') =>
  `${currency} ${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const formatError = (error: any) => {
  const data = error?.response?.data;
  return data?.detail || data?.error?.message || data?.error?.details?.detail || 'Unable to load reporting data.';
};

const csvValue = (value: string | number) => `"${String(value).replace(/"/g, '""')}"`;

export const Reports: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [showExceptions, setShowExceptions] = useState(false);

  const fetchReportData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const [invoiceResponse, paymentResponse] = await Promise.all([
        api.get('/invoices/?page_size=100'),
        api.get('/payments/?page_size=100'),
      ]);
      setInvoices(invoiceResponse.data?.results || []);
      setPayments(paymentResponse.data?.results || []);
    } catch (requestError) {
      setError(formatError(requestError));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, []);

  const agingBuckets = useMemo<AgingBucket[]>(() => {
    const today = new Date();
    const buckets: AgingBucket[] = [
      { label: '0–30 days', count: 0, amount: 0 },
      { label: '31–60 days', count: 0, amount: 0 },
      { label: '61–90 days', count: 0, amount: 0 },
      { label: '90+ days', count: 0, amount: 0 },
    ];
    invoices
      .filter((invoice) => !['PAID', 'CANCELLED'].includes(invoice.payment_status))
      .forEach((invoice) => {
        const referenceDate = invoice.due_date || invoice.invoice_date;
        if (!referenceDate) return;
        const days = Math.max(0, Math.floor((today.getTime() - new Date(referenceDate).getTime()) / 86400000));
        const index = days <= 30 ? 0 : days <= 60 ? 1 : days <= 90 ? 2 : 3;
        buckets[index].count += 1;
        buckets[index].amount += Number(invoice.total_amount || 0);
      });
    return buckets;
  }, [invoices]);

  const statusSummary = useMemo(() => {
    const statuses = ['PENDING', 'APPROVED', 'PAID', 'REJECTED', 'EXCEPTION'];
    return statuses.map((status) => ({
      status,
      count: invoices.filter((invoice) => {
        if (status === 'EXCEPTION') return invoice.processing_status === 'EXCEPTION' || invoice.validation_status === 'FAILED';
        if (status === 'PAID') return invoice.payment_status === 'PAID';
        if (status === 'APPROVED') return invoice.approval_status === 'APPROVED';
        if (status === 'REJECTED') return invoice.approval_status === 'REJECTED';
        return invoice.approval_status === 'PENDING' || invoice.processing_status === 'UPLOADED';
      }).length,
    }));
  }, [invoices]);

  const gstSummary = useMemo(() => ({
    subtotal: invoices.reduce((total, invoice) => total + Number(invoice.subtotal || 0), 0),
    tax: invoices.reduce((total, invoice) => total + Number(invoice.tax_amount || 0), 0),
    total: invoices.reduce((total, invoice) => total + Number(invoice.total_amount || 0), 0),
    gstinMatched: invoices.filter((invoice) => Boolean(invoice.vendor_gstin_extracted)).length,
  }), [invoices]);

  const exceptions = useMemo(() => invoices.flatMap((invoice) => (
    (invoice.validation_results || [])
      .filter((result) => result.severity === 'FAILED')
      .map((result) => ({ invoice, result }))
  )), [invoices]);

  const paymentSummary = useMemo(() => ({
    requested: payments.filter((payment) => payment.status === 'REQUESTED').reduce((total, payment) => total + Number(payment.amount || 0), 0),
    paid: payments.filter((payment) => payment.status === 'PAID').reduce((total, payment) => total + Number(payment.amount || 0), 0),
  }), [payments]);

  const exportCsv = () => {
    const rows = [
      ['Invoice Number', 'Vendor', 'Invoice Date', 'Due Date', 'Subtotal', 'Tax', 'Total', 'Approval Status', 'Payment Status', 'Processing Status'],
      ...invoices.map((invoice) => [
        invoice.invoice_number,
        invoice.vendor_name || '',
        invoice.invoice_date || '',
        invoice.due_date || '',
        invoice.subtotal,
        invoice.tax_amount,
        invoice.total_amount,
        invoice.approval_status,
        invoice.payment_status,
        invoice.processing_status,
      ]),
    ];
    const csv = rows.map((row) => row.map(csvValue).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'ap-invoice-report.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Financial & Compliance Reports</h1>
          <p className="text-sm text-slate-400">AP aging, invoice status, GST reconciliation, and workflow exceptions.</p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={exportCsv} disabled={!invoices.length} className="inline-flex items-center gap-2 rounded-lg border border-slate-600 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50">
            <Download className="h-4 w-4" /> Export CSV
          </button>
          <button type="button" onClick={() => fetchReportData(true)} disabled={refreshing} className="inline-flex items-center gap-2 rounded-lg border border-slate-600 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>
      </div>

      {error && <div className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert"><AlertCircle className="h-4 w-4" />{error}</div>}

      {loading ? (
        <div className="rounded-2xl border border-slate-700/60 bg-slate-800/80 p-10 text-center text-sm text-slate-500">Loading reporting data...</div>
      ) : invoices.length === 0 ? (
        <div className="rounded-2xl border border-slate-700/60 bg-slate-800/80 p-10 text-center"><BarChart3 className="mx-auto mb-3 h-10 w-10 text-slate-500" /><p className="text-sm font-medium text-white">No invoice data available for reporting.</p><p className="mt-1 text-xs text-slate-500">Reports will populate as invoices enter the workflow.</p></div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {agingBuckets.map((bucket) => <div key={bucket.label} className="rounded-xl border border-slate-700/60 bg-slate-800/80 p-4"><p className="text-xs uppercase tracking-wide text-slate-500">{bucket.label}</p><p className="mt-2 text-2xl font-bold text-white">{bucket.count}</p><p className="mt-1 text-xs text-slate-400">{formatMoney(bucket.amount)}</p></div>)}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-2xl border border-slate-700/60 bg-slate-800/80 p-5">
              <div className="flex items-center justify-between"><div><h2 className="font-semibold text-white">Invoice status summary</h2><p className="mt-1 text-xs text-slate-500">Current workflow status across invoices</p></div><CheckCircle2 className="h-5 w-5 text-emerald-400" /></div>
              <div className="mt-5 space-y-3">{statusSummary.map((item) => <div key={item.status} className="flex items-center justify-between rounded-lg bg-slate-900/50 px-3 py-2"><span className="text-sm text-slate-300">{item.status.replace('_', ' ')}</span><span className="font-semibold text-white">{item.count}</span></div>)}</div>
              <div className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-700/60 pt-4"><div><p className="text-xs text-slate-500">Payment requested</p><p className="mt-1 font-semibold text-amber-300">{formatMoney(paymentSummary.requested)}</p></div><div><p className="text-xs text-slate-500">Paid</p><p className="mt-1 font-semibold text-emerald-300">{formatMoney(paymentSummary.paid)}</p></div></div>
            </section>

            <section className="rounded-2xl border border-slate-700/60 bg-slate-800/80 p-5">
              <div className="flex items-center justify-between"><div><h2 className="font-semibold text-white">GST / ITC reconciliation</h2><p className="mt-1 text-xs text-slate-500">Derived from invoice tax and vendor GSTIN data</p></div><span className="text-xs text-cyan-300">{gstSummary.gstinMatched}/{invoices.length} GSTIN present</span></div>
              <div className="mt-5 grid grid-cols-3 gap-3"><div><p className="text-xs text-slate-500">Subtotal</p><p className="mt-1 text-sm font-semibold text-white">{formatMoney(gstSummary.subtotal)}</p></div><div><p className="text-xs text-slate-500">Input tax</p><p className="mt-1 text-sm font-semibold text-cyan-300">{formatMoney(gstSummary.tax)}</p></div><div><p className="text-xs text-slate-500">Gross total</p><p className="mt-1 text-sm font-semibold text-white">{formatMoney(gstSummary.total)}</p></div></div>
              <div className="mt-5 rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3 text-xs text-slate-400">Potential ITC is represented by invoice tax amounts where vendor GSTIN data is available. Final tax filing reconciliation should be reviewed against statutory records.</div>
            </section>
          </div>

          <section className="rounded-2xl border border-rose-500/20 bg-slate-800/80 p-5">
            <div className="flex items-center justify-between"><div><h2 className="font-semibold text-white">Workflow exceptions</h2><p className="mt-1 text-xs text-slate-500">{exceptions.length} failed validation rule{exceptions.length === 1 ? '' : 's'}</p></div><button type="button" onClick={() => setShowExceptions(true)} disabled={!exceptions.length} className="rounded-lg border border-slate-600 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50">View details</button></div>
            {exceptions.length === 0 && <p className="mt-4 flex items-center gap-2 text-sm text-emerald-300"><CheckCircle2 className="h-4 w-4" />No failed validation rules in the current invoice set.</p>}
          </section>
        </>
      )}

      {showExceptions && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4"><div className="w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-800 p-6 shadow-2xl"><div className="flex items-start justify-between"><div><p className="text-xs uppercase tracking-wide text-rose-400">Exception report</p><h2 className="mt-1 text-xl font-bold text-white">Validation failures</h2></div><button type="button" onClick={() => setShowExceptions(false)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-700 hover:text-white" aria-label="Close exceptions"><X className="h-5 w-5" /></button></div><div className="mt-5 space-y-3">{exceptions.map(({ invoice, result }) => <div key={`${invoice.id}-${result.rule_code}`} className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-3"><p className="font-mono text-xs text-rose-300">{invoice.invoice_number} · {result.rule_code}</p><p className="mt-1 text-sm text-slate-300">{result.message}</p></div>)}</div></div></div>}
    </div>
  );
};
