import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, ChevronDown, Clock, RefreshCw, X, XCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';

type ApprovalRequest = {
  id: string;
  invoice: string;
  invoice_number: string;
  invoice_total: string;
  status: string;
  current_step: number;
  total_steps: number;
  submitted_by: string | null;
  required_role: string | null;
  actions: Array<{
    id: string;
    action: string;
    comments: string;
    actor_email: string;
    created_at: string;
  }>;
  created_at: string;
};

type InvoiceDetails = {
  vendor_name?: string;
  vendor_code?: string;
  po_number?: string;
  purchase_order?: string;
  total_amount?: string;
  currency?: string;
  invoice_date?: string;
  due_date?: string;
  processing_status?: string;
  matching_status?: string;
};

const approverRoles = ['APPROVER', 'FINANCE', 'CFO', 'ADMIN'];
const inputClass = 'w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500';

const formatError = (error: any) => {
  const data = error?.response?.data;
  if (!data) return 'Unable to complete the approval action.';
  return data?.error?.message || data?.detail || data?.error?.details?.detail || 'Unable to complete the approval action.';
};

export const Approvals: React.FC = () => {
  const { user } = useAuth();
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [invoiceDetails, setInvoiceDetails] = useState<Record<string, InvoiceDetails>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [commentRequest, setCommentRequest] = useState<ApprovalRequest | null>(null);
  const [comment, setComment] = useState('');
  const [action, setAction] = useState<'approve' | 'reject' | null>(null);
  const [actionError, setActionError] = useState('');
  const [saving, setSaving] = useState(false);

  const canAct = user?.role ? approverRoles.includes(user.role) : false;

  const fetchRequests = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const response = await api.get('/approvals/?status=PENDING');
      const result: ApprovalRequest[] = response.data?.results || [];
      const relevant = result.filter((request) => (
        user?.role === 'ADMIN' ||
        request.required_role === user?.role ||
        request.submitted_by === user?.id
      ));
      setRequests(relevant);

      const details = await Promise.all(
        relevant
          .filter((request) => !invoiceDetails[request.invoice])
          .map(async (request) => {
            try {
              const invoiceResponse = await api.get(`/invoices/${request.invoice}/`);
              return [request.invoice, invoiceResponse.data] as const;
            } catch {
              return [request.invoice, {}] as const;
            }
          }),
      );
      if (details.length) {
        setInvoiceDetails((current) => ({ ...current, ...Object.fromEntries(details) }));
      }
    } catch (requestError) {
      setError(formatError(requestError));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [user?.id, user?.role]);

  const openAction = (request: ApprovalRequest, nextAction: 'approve' | 'reject') => {
    setCommentRequest(request);
    setAction(nextAction);
    setComment('');
    setActionError('');
  };

  const submitAction = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!commentRequest || !action || saving) return;
    if (action === 'reject' && !comment.trim()) {
      setActionError('Please provide a rejection reason.');
      return;
    }
    setSaving(true);
    setActionError('');
    try {
      await api.post(`/approvals/${commentRequest.id}/${action}/`, { comments: comment });
      setCommentRequest(null);
      setAction(null);
      await fetchRequests(true);
    } catch (requestError) {
      setActionError(formatError(requestError));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Approval Queue & Workflow</h1>
          <p className="text-sm text-slate-400">Review invoices routed to your role by the approval matrix.</p>
        </div>
        <button type="button" onClick={() => fetchRequests(true)} disabled={refreshing} className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-600 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50">
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {error && <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert">{error}</div>}

      <div className="flex items-center gap-3 rounded-xl border border-slate-700/60 bg-slate-800/80 px-4 py-3">
        <Clock className="h-5 w-5 text-amber-400" />
        <div>
          <p className="text-sm font-semibold text-white">{requests.length} pending request{requests.length === 1 ? '' : 's'}</p>
          <p className="text-xs text-slate-400">Your role: <span className="text-amber-300">{user?.role || 'Unknown'}</span></p>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-800/80 shadow-lg">
        {loading ? (
          <div className="p-10 text-center text-sm text-slate-500">Loading approval queue...</div>
        ) : requests.length === 0 ? (
          <div className="p-10 text-center">
            <CheckCircle2 className="mx-auto mb-3 h-10 w-10 text-emerald-400" />
            <p className="text-sm font-medium text-white">No approval requests are currently routed to you.</p>
            <p className="mt-1 text-xs text-slate-500">Requests appear here when validation, matching, and the approval matrix routing complete.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/60">
            {requests.map((request) => {
              const invoice = invoiceDetails[request.invoice] || {};
              const isExpanded = expandedId === request.id;
              const isActionable = canAct && request.required_role === user?.role && request.submitted_by !== user?.id;
              return (
                <div key={request.id} className="p-5">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <button type="button" onClick={() => setExpandedId(isExpanded ? null : request.id)} className="flex min-w-0 items-start gap-3 text-left">
                      <ChevronDown className={`mt-1 h-4 w-4 shrink-0 text-slate-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      <span className="min-w-0">
                        <span className="block truncate font-semibold text-white">{request.invoice_number || 'Invoice pending OCR'}</span>
                        <span className="mt-1 block text-xs text-slate-400">{invoice.vendor_name || 'Vendor unavailable'} · {invoice.po_number || 'No PO reference'}</span>
                      </span>
                    </button>
                    <div className="flex flex-wrap items-center gap-3 lg:justify-end">
                      <span className="text-lg font-semibold text-emerald-400">{invoice.currency || 'INR'} {request.invoice_total}</span>
                      <span className="rounded-full border border-amber-500/20 bg-amber-500/10 px-2 py-1 text-[10px] font-semibold text-amber-300">STEP {request.current_step}/{request.total_steps}</span>
                      {isActionable ? (
                        <>
                          <button type="button" onClick={() => openAction(request, 'approve')} className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-500"><CheckCircle2 className="h-4 w-4" /> Approve</button>
                          <button type="button" onClick={() => openAction(request, 'reject')} className="inline-flex items-center gap-1 rounded-lg border border-rose-500/40 px-3 py-2 text-xs font-semibold text-rose-300 hover:bg-rose-500/10"><XCircle className="h-4 w-4" /> Reject</button>
                        </>
                      ) : (
                        <span className="text-xs text-slate-500">Awaiting {request.required_role || 'configured approver'}</span>
                      )}
                    </div>
                  </div>
                  {isExpanded && (
                    <div className="mt-4 grid gap-3 rounded-xl border border-slate-700 bg-slate-900/50 p-4 text-xs sm:grid-cols-2 lg:grid-cols-4">
                      <div><p className="text-slate-500">Invoice date</p><p className="mt-1 text-slate-200">{invoice.invoice_date || '—'}</p></div>
                      <div><p className="text-slate-500">Due date</p><p className="mt-1 text-slate-200">{invoice.due_date || '—'}</p></div>
                      <div><p className="text-slate-500">PO reference</p><p className="mt-1 font-mono text-slate-200">{invoice.po_number || '—'}</p></div>
                      <div><p className="text-slate-500">Matching status</p><p className="mt-1 text-slate-200">{invoice.matching_status || '—'}</p></div>
                      <div><p className="text-slate-500">Processing status</p><p className="mt-1 text-slate-200">{invoice.processing_status || '—'}</p></div>
                      <div><p className="text-slate-500">Required role</p><p className="mt-1 text-amber-300">{request.required_role || '—'}</p></div>
                      <div><p className="text-slate-500">Submitted</p><p className="mt-1 text-slate-200">{new Date(request.created_at).toLocaleString()}</p></div>
                      <div><p className="text-slate-500">Actions</p><p className="mt-1 text-slate-200">{request.actions.length}</p></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {commentRequest && action && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-700 px-6 py-4">
              <div>
                <h2 className="text-lg font-bold text-white">{action === 'approve' ? 'Approve invoice' : 'Reject invoice'}</h2>
                <p className="mt-1 text-xs text-slate-400">{commentRequest.invoice_number || 'Invoice review'}</p>
              </div>
              <button type="button" onClick={() => !saving && setCommentRequest(null)} disabled={saving} className="rounded-lg p-2 text-slate-400 hover:bg-slate-700 hover:text-white disabled:opacity-50" aria-label="Close">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={submitAction} className="space-y-4 p-6">
              {actionError && <div className="flex gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300"><AlertCircle className="h-4 w-4 shrink-0" />{actionError}</div>}
              <label className="block">
                <span className="mb-1.5 block text-xs font-medium text-slate-300">{action === 'reject' ? 'Rejection reason *' : 'Comment'}</span>
                <textarea required={action === 'reject'} rows={4} value={comment} onChange={(event) => setComment(event.target.value)} className={inputClass} placeholder={action === 'reject' ? 'Explain why this invoice is being rejected.' : 'Add an optional review comment.'} />
              </label>
              <div className="flex justify-end gap-3 border-t border-slate-700 pt-4">
                <button type="button" onClick={() => setCommentRequest(null)} disabled={saving} className="rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-50">Cancel</button>
                <button type="submit" disabled={saving} className={`rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 ${action === 'approve' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-rose-600 hover:bg-rose-500'}`}>{saving ? 'Saving...' : action === 'approve' ? 'Confirm approval' : 'Confirm rejection'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
