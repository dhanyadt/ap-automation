import React, { useEffect, useState } from 'react';
import { FileText, Search, Plus, X, UploadCloud } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

type InvoiceForm = {
  file: File | null;
  vendor: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  purchase_order: string;
  currency: string;
};

const initialForm: InvoiceForm = {
  file: null,
  vendor: '',
  invoice_number: '',
  invoice_date: new Date().toISOString().slice(0, 10),
  due_date: '',
  purchase_order: '',
  currency: 'INR',
};

const inputClass = 'w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500';
const labelClass = 'mb-1.5 block text-xs font-medium text-slate-300';
const acceptedExtensions = ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'tif'];

const formatApiError = (error: any): string => {
  const data = error?.response?.data;
  if (!data) return 'Unable to upload invoice. Please try again.';
  if (typeof data === 'string') return data;
  return Object.entries(data).map(([field, value]) => {
    const message = Array.isArray(value) ? value.join(', ') : String(value);
    return `${field === 'non_field_errors' ? 'Error' : field}: ${message}`;
  }).join(' | ');
};

export const Invoices: React.FC = () => {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [vendors, setVendors] = useState<any[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState<InvoiceForm>(initialForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const canUpload = user?.role === 'AP_CLERK' || user?.role === 'ADMIN';

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

  const openModal = async () => {
    setForm(initialForm);
    setFormError('');
    setIsModalOpen(true);
    try {
      const [vendorResponse, poResponse] = await Promise.all([
        api.get('/vendors/?status=ACTIVE'),
        api.get('/purchase-orders/?status=ISSUED'),
      ]);
      setVendors(vendorResponse.data?.results || []);
      setPurchaseOrders(poResponse.data?.results || []);
    } catch (error) {
      setFormError('Unable to load active vendors or issued purchase orders. Please close and try again.');
    }
  };

  const submitInvoice = async (event: React.FormEvent) => {
    event.preventDefault();
    if (saving || !form.file) return;
    setSaving(true);
    setFormError('');

    try {
      const uploadData = new FormData();
      uploadData.append('file', form.file);
      if (form.vendor) uploadData.append('vendor', form.vendor);
      if (form.purchase_order) {
        const selectedPO = purchaseOrders.find((po) => po.id === form.purchase_order);
        if (selectedPO?.po_number) uploadData.append('po_number', selectedPO.po_number);
      }

      const uploadResponse = await api.post('/invoices/upload/', uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const uploadedInvoice = uploadResponse.data?.data;
      const metadata = Object.fromEntries(
        Object.entries({
          invoice_number: form.invoice_number,
          invoice_date: form.invoice_date,
          due_date: form.due_date,
          currency: form.currency,
          purchase_order: form.purchase_order || undefined,
        }).filter(([, value]) => value !== '' && value !== undefined),
      );

      if (uploadedInvoice?.id && Object.keys(metadata).length > 0) {
        await api.patch(`/invoices/${uploadedInvoice.id}/`, metadata);
      }

      setIsModalOpen(false);
      setForm(initialForm);
      await fetchInvoices();
    } catch (error) {
      setFormError(formatApiError(error));
    } finally {
      setSaving(false);
    }
  };

  const selectFile = (file: File | undefined) => {
    if (!file) return;
    const extension = file.name.split('.').pop()?.toLowerCase() || '';
    if (!acceptedExtensions.includes(extension)) {
      setFormError('Unsupported file format. Use PDF, JPG, JPEG, PNG, TIFF, or TIF.');
      return;
    }
    setForm((current) => ({ ...current, file }));
    setFormError('');
  };

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
        {canUpload && (
          <button type="button" onClick={openModal} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-900/20 hover:bg-blue-500">
            <Plus className="h-4 w-4" /> Upload Invoice
          </button>
        )}
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

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-700 px-6 py-4">
              <div>
                <h2 className="text-lg font-bold text-white">Upload Invoice</h2>
                <p className="mt-1 text-xs text-slate-400">Upload a PDF or supported invoice image for processing.</p>
              </div>
              <button type="button" onClick={() => !saving && setIsModalOpen(false)} disabled={saving} className="rounded-lg p-2 text-slate-400 hover:bg-slate-700 hover:text-white disabled:opacity-50" aria-label="Close modal">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={submitInvoice} className="space-y-5 p-6">
              {formError && <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert">{formError}</div>}
              <div
                onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(event) => { event.preventDefault(); setIsDragging(false); selectFile(event.dataTransfer.files?.[0]); }}
                className={`rounded-xl border-2 border-dashed p-5 text-center transition-colors ${isDragging ? 'border-blue-400 bg-blue-500/10' : 'border-slate-600 bg-slate-900/50'}`}
              >
                <span className={labelClass}>Invoice document *</span>
                <UploadCloud className="mx-auto my-2 h-7 w-7 text-blue-400" />
                <label className="inline-flex cursor-pointer items-center rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-500">
                  Choose file
                  <input required={!form.file} type="file" accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif" onChange={(event) => selectFile(event.target.files?.[0])} className="sr-only" />
                </label>
                <span className="mt-2 block text-[11px] text-slate-500">or drag and drop · PDF, JPG, JPEG, PNG, TIFF, TIF</span>
                {form.file && <p className="mt-3 text-xs text-slate-300">{form.file.name} <span className="text-slate-500">({(form.file.size / 1024 / 1024).toFixed(2)} MB)</span></p>}
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <label><span className={labelClass}>Vendor</span><select value={form.vendor} onChange={(e) => setForm({ ...form, vendor: e.target.value, purchase_order: '' })} className={inputClass}><option value="">Select active vendor</option>{vendors.map((vendor) => <option key={vendor.id} value={vendor.id}>{vendor.code} - {vendor.name}</option>)}</select></label>
                <label><span className={labelClass}>Purchase order</span><select value={form.purchase_order} onChange={(e) => setForm({ ...form, purchase_order: e.target.value })} className={inputClass}><option value="">No PO reference</option>{purchaseOrders.filter((po) => !form.vendor || po.vendor === form.vendor).map((po) => <option key={po.id} value={po.id}>{po.po_number} - {po.vendor_name}</option>)}</select></label>
                <label><span className={labelClass}>Invoice number</span><input value={form.invoice_number} onChange={(e) => setForm({ ...form, invoice_number: e.target.value })} className={inputClass} /></label>
                <label><span className={labelClass}>Currency</span><input maxLength={3} value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })} className={inputClass} /></label>
                <label><span className={labelClass}>Invoice date</span><input type="date" value={form.invoice_date} onChange={(e) => setForm({ ...form, invoice_date: e.target.value })} className={inputClass} /></label>
                <label><span className={labelClass}>Due date</span><input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className={inputClass} /></label>
              </div>
              <div className="flex items-center gap-2 rounded-lg border border-blue-500/20 bg-blue-500/10 p-3 text-xs text-blue-200">
                <FileText className="h-4 w-4 shrink-0" />
                {saving ? 'Uploading document and saving invoice details...' : form.file ? `Ready to upload ${form.file.name}` : 'Choose an invoice document to begin.'}
              </div>
              <div className="flex justify-end gap-3 border-t border-slate-700 pt-5">
                <button type="button" onClick={() => setIsModalOpen(false)} disabled={saving} className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50">Cancel</button>
                <button type="submit" disabled={saving || !form.file} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50">{saving ? 'Uploading...' : 'Upload Invoice'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
