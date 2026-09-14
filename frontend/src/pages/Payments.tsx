import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, CreditCard, FileText, Loader2, Printer, RefreshCw, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';

type Payment = {
  id: string;
  invoice: string;
  invoice_number: string;
  vendor: string;
  vendor_name: string;
  amount: string;
  currency: string;
  payment_method: string;
  status: 'REQUESTED' | 'PROCESSING' | 'PAID' | 'FAILED' | 'CANCELLED' | string;
  reference_number: string;
  paid_at: string | null;
  created_at: string;
  advice?: PaymentAdvice;
};

type PaymentAdvice = {
  payment_id: string;
  invoice_number: string;
  invoice_date: string | null;
  vendor_name: string;
  vendor_code: string;
  amount: string;
  currency: string;
  payment_method: string;
  status: string;
  utr: string | null;
  paid_at: string | null;
  advice_notes: string;
};

const financeRoles = ['FINANCE', 'CFO', 'ADMIN'];

const formatError = (error: any) => {
  const data = error?.response?.data;
  return data?.detail || data?.error?.message || data?.error?.details?.detail || 'Unable to complete the payment request.';
};

const formatDate = (value: string | null) => value
  ? new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(value))
  : '—';

const statusStyles: Record<string, string> = {
  REQUESTED: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  PROCESSING: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
  PAID: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  FAILED: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
  CANCELLED: 'border-slate-600 bg-slate-700/50 text-slate-300',
};

export const Payments: React.FC = () => {
  const { user } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [advice, setAdvice] = useState<PaymentAdvice | null>(null);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');

  const canProcess = user?.role ? financeRoles.includes(user.role) : false;

  const fetchPayments = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const response = await api.get('/payments/');
      setPayments(response.data?.results || []);
    } catch (requestError) {
      setError(formatError(requestError));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const processPayment = async (payment: Payment) => {
    if (processingId) return;
    setProcessingId(payment.id);
    setActionError('');
    try {
      await api.post(`/payments/${payment.id}/process/`);
      await fetchPayments(true);
    } catch (requestError) {
      setActionError(formatError(requestError));
    } finally {
      setProcessingId(null);
    }
  };

  const viewAdvice = async (payment: Payment) => {
    setActionError('');
    try {
      const response = await api.get(`/payments/${payment.id}/advice/`);
      setAdvice(response.data);
    } catch (requestError) {
      setActionError(formatError(requestError));
    }
  };

  const printAdvice = () => {
    if (!advice) return;
    const printWindow = window.open('', '_blank', 'width=800,height=700');
    if (!printWindow) return;
    printWindow.document.write(`<html><head><title>Payment Advice - ${advice.invoice_number}</title><style>body{font-family:Arial,sans-serif;padding:40px;color:#172033}h1{font-size:24px}table{width:100%;border-collapse:collapse;margin-top:24px}td{padding:12px;border-bottom:1px solid #ddd}td:first-child{font-weight:bold;width:35%;color:#526070}</style></head><body><h1>Payment Advice</h1><p>Invoice ${advice.invoice_number}</p><table><tbody><tr><td>Vendor</td><td>${advice.vendor_name}</td></tr><tr><td>Amount</td><td>${advice.currency} ${advice.amount}</td></tr><tr><td>Status</td><td>${advice.status}</td></tr><tr><td>Payment method</td><td>${advice.payment_method}</td></tr><tr><td>UTR / Reference</td><td>${advice.utr || 'Not settled'}</td></tr><tr><td>Paid date</td><td>${advice.paid_at ? formatDate(advice.paid_at) : 'Not settled'}</td></tr></tbody></table></body></html>`);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  };

  const totalRequested = payments
    .filter((payment) => payment.status === 'REQUESTED')
    .reduce((total, payment) => total + Number(payment.amount), 0);
  const totalPaid = payments
    .filter((payment) => payment.status === 'PAID')
    .reduce((total, payment) => total + Number(payment.amount), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Payment Disbursements & Advice</h1>
          <p className="text-sm text-slate-400">Track approved invoice payments, settlement references, and payment advice.</p>
        </div>
        <button
          type="button"
          onClick={() => fetchPayments(true)}
          disabled={refreshing}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-600 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
      {actionError && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {actionError}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-700/60 bg-slate-800/80 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Payment records</p>
          <p className="mt-2 text-2xl font-bold text-white">{payments.length}</p>
        </div>
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
          <p className="text-xs uppercase tracking-wide text-amber-300/70">Awaiting processing</p>
          <p className="mt-2 text-2xl font-bold text-amber-300">₹{totalRequested.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
        </div>
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
          <p className="text-xs uppercase tracking-wide text-emerald-300/70">Settled</p>
          <p className="mt-2 text-2xl font-bold text-emerald-300">₹{totalPaid.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-800/80 shadow-lg">
        {loading ? (
          <div className="p-10 text-center text-sm text-slate-500">Loading payment records...</div>
        ) : payments.length === 0 ? (
          <div className="p-10 text-center">
            <CreditCard className="mx-auto mb-3 h-10 w-10 text-slate-500" />
            <p className="text-sm font-medium text-white">No payment records found.</p>
            <p className="mt-1 text-xs text-slate-500">Payments appear here after an approved invoice enters the payment stage.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-700/60 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-4 font-medium">Invoice / Vendor</th>
                  <th className="px-5 py-4 font-medium">Amount</th>
                  <th className="px-5 py-4 font-medium">Status</th>
                  <th className="px-5 py-4 font-medium">Requested</th>
                  <th className="px-5 py-4 font-medium">UTR / Reference</th>
                  <th className="px-5 py-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {payments.map((payment) => (
                  <tr key={payment.id} className="text-slate-300">
                    <td className="px-5 py-4">
                      <p className="font-semibold text-white">{payment.invoice_number || 'Invoice pending OCR'}</p>
                      <p className="mt-1 text-xs text-slate-500">{payment.vendor_name || 'Vendor unavailable'}</p>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 font-medium text-white">
                      {payment.currency} {Number(payment.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      <p className="mt-1 text-xs text-slate-500">{payment.payment_method}</p>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${statusStyles[payment.status] || statusStyles.CANCELLED}`}>
                        {payment.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-400">{formatDate(payment.created_at)}</td>
                    <td className="px-5 py-4 font-mono text-xs text-slate-400">{payment.reference_number || 'Not settled'}</td>
                    <td className="px-5 py-4">
                      <div className="flex justify-end gap-2">
                        {canProcess && payment.status === 'REQUESTED' && (
                          <button
                            type="button"
                            onClick={() => processPayment(payment)}
                            disabled={processingId !== null}
                            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {processingId === payment.id && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                            Process payment
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => viewAdvice(payment)}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-600 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700"
                        >
                          <FileText className="h-3.5 w-3.5" />
                          Advice
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {advice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-800 p-6 shadow-2xl">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-wide text-cyan-400">Payment advice</p>
                <h2 className="mt-1 text-xl font-bold text-white">{advice.invoice_number}</h2>
              </div>
              <button type="button" onClick={printAdvice} className="mr-2 inline-flex items-center gap-1.5 rounded-lg border border-slate-600 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-700"><Printer className="h-3.5 w-3.5" /> Print</button>
              <button type="button" onClick={() => setAdvice(null)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-700 hover:text-white" aria-label="Close advice">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div><p className="text-xs text-slate-500">Vendor</p><p className="mt-1 text-sm text-white">{advice.vendor_name}</p></div>
              <div><p className="text-xs text-slate-500">Amount</p><p className="mt-1 text-sm text-white">{advice.currency} {Number(advice.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p></div>
              <div><p className="text-xs text-slate-500">Payment method</p><p className="mt-1 text-sm text-white">{advice.payment_method}</p></div>
              <div><p className="text-xs text-slate-500">Status</p><p className="mt-1 text-sm text-white">{advice.status.replace('_', ' ')}</p></div>
              <div className="sm:col-span-2"><p className="text-xs text-slate-500">UTR / Reference</p><p className="mt-1 break-all font-mono text-sm text-cyan-300">{advice.utr || 'Not settled'}</p></div>
              <div className="sm:col-span-2"><p className="text-xs text-slate-500">Paid date</p><p className="mt-1 text-sm text-white">{formatDate(advice.paid_at)}</p></div>
            </div>
            {advice.advice_notes && <p className="mt-5 rounded-lg bg-slate-900/60 p-3 text-xs text-slate-400">{advice.advice_notes}</p>}
          </div>
        </div>
      )}
    </div>
  );
};
