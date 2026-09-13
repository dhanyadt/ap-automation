import React, { useEffect, useState } from 'react';
import { Plus, Search, X, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

type POItem = {
  item_code: string;
  description: string;
  quantity: number;
  unit_of_measure: string;
  unit_price: number;
  tax_rate: number;
};

type POForm = {
  po_number: string;
  vendor: string;
  status: string;
  currency: string;
  issue_date: string;
  delivery_date: string;
  notes: string;
  items: POItem[];
};

const emptyItem = (): POItem => ({
  item_code: '',
  description: '',
  quantity: 1,
  unit_of_measure: 'NOS',
  unit_price: 0,
  tax_rate: 18,
});

const initialForm: POForm = {
  po_number: '',
  vendor: '',
  status: 'ISSUED',
  currency: 'INR',
  issue_date: new Date().toISOString().slice(0, 10),
  delivery_date: '',
  notes: '',
  items: [emptyItem()],
};

const labelClass = 'mb-1.5 block text-xs font-medium text-slate-300';
const inputClass = 'w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500';

const formatApiError = (error: any): string => {
  const data = error?.response?.data;
  if (!data) return 'Unable to create purchase order. Please try again.';
  if (typeof data === 'string') return data;
  return Object.entries(data).map(([field, value]) => {
    const message = Array.isArray(value) ? value.join(', ') : String(value);
    return `${field === 'non_field_errors' ? 'Error' : field}: ${message}`;
  }).join(' | ');
};

export const PurchaseOrders: React.FC = () => {
  const { user } = useAuth();
  const [pos, setPos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [vendors, setVendors] = useState<any[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState<POForm>(initialForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const canCreate = user?.role === 'AP_CLERK' || user?.role === 'ADMIN';

  const fetchPOs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/purchase-orders/');
      setPos(res.data?.results || []);
    } catch (err) {
      console.error('Failed to load purchase orders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPOs();
  }, []);

  const openModal = async () => {
    setForm(initialForm);
    setFormError('');
    setIsModalOpen(true);
    try {
      const res = await api.get('/vendors/?status=ACTIVE');
      setVendors(res.data?.results || []);
    } catch (error) {
      setFormError('Unable to load active vendors. Please close and try again.');
    }
  };

  const updateItem = (index: number, field: keyof POItem, value: string | number) => {
    setForm((current) => ({
      ...current,
      items: current.items.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item),
    }));
  };

  const subtotal = form.items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0);
  const taxAmount = form.items.reduce((sum, item) => sum + (item.quantity * item.unit_price * item.tax_rate) / 100, 0);
  const totalAmount = subtotal + taxAmount;

  const submitPO = async (event: React.FormEvent) => {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    setFormError('');
    try {
      await api.post('/purchase-orders/', {
        ...form,
        delivery_date: form.delivery_date || null,
        subtotal: subtotal.toFixed(2),
        tax_amount: taxAmount.toFixed(2),
        total_amount: totalAmount.toFixed(2),
        items: form.items.map((item, index) => ({ ...item, line_number: index + 1 })),
      });
      setIsModalOpen(false);
      await fetchPOs();
    } catch (error) {
      setFormError(formatApiError(error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Purchase Orders (PO)</h1>
          <p className="text-sm text-slate-400">Manage issued purchase orders and line items for 2-way and 3-way matching</p>
        </div>
        {canCreate && (
          <button type="button" onClick={openModal} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-900/20 hover:bg-blue-500">
            <Plus className="h-4 w-4" /> Add Purchase Order
          </button>
        )}
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

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-slate-700 bg-slate-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-700 px-6 py-4">
              <div>
                <h2 className="text-lg font-bold text-white">Add Purchase Order</h2>
                <p className="mt-1 text-xs text-slate-400">Create a PO with line items for matching.</p>
              </div>
              <button type="button" onClick={() => !saving && setIsModalOpen(false)} disabled={saving} className="rounded-lg p-2 text-slate-400 hover:bg-slate-700 hover:text-white disabled:opacity-50" aria-label="Close modal">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={submitPO} className="space-y-5 p-6">
              {formError && <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert">{formError}</div>}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <label><span className={labelClass}>PO number *</span><input required value={form.po_number} onChange={(e) => setForm({ ...form, po_number: e.target.value })} className={inputClass} /></label>
                <label><span className={labelClass}>Vendor *</span><select required value={form.vendor} onChange={(e) => setForm({ ...form, vendor: e.target.value })} className={inputClass}><option value="">Select vendor</option>{vendors.map((vendor) => <option key={vendor.id} value={vendor.id}>{vendor.code} - {vendor.name}</option>)}</select></label>
                <label><span className={labelClass}>Issue date *</span><input required type="date" value={form.issue_date} onChange={(e) => setForm({ ...form, issue_date: e.target.value })} className={inputClass} /></label>
                <label><span className={labelClass}>Delivery date</span><input type="date" value={form.delivery_date} onChange={(e) => setForm({ ...form, delivery_date: e.target.value })} className={inputClass} /></label>
                <label><span className={labelClass}>Status</span><select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className={inputClass}><option value="ISSUED">Issued</option><option value="DRAFT">Draft</option></select></label>
                <label><span className={labelClass}>Currency</span><input value={form.currency} maxLength={3} onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })} className={inputClass} /></label>
              </div>

              <div>
                <div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-semibold text-white">Line items</h3><button type="button" onClick={() => setForm({ ...form, items: [...form.items, emptyItem()] })} className="text-xs font-semibold text-blue-400 hover:text-blue-300"><Plus className="mr-1 inline h-3 w-3" /> Add line</button></div>
                <div className="space-y-3">
                  {form.items.map((item, index) => (
                    <div key={index} className="grid gap-3 rounded-xl border border-slate-700 bg-slate-900/50 p-3 sm:grid-cols-2 lg:grid-cols-7">
                      <input required placeholder="Description" value={item.description} onChange={(e) => updateItem(index, 'description', e.target.value)} className={`${inputClass} lg:col-span-2`} />
                      <input placeholder="Item code" value={item.item_code} onChange={(e) => updateItem(index, 'item_code', e.target.value)} className={inputClass} />
                      <input required type="number" min="0.01" step="0.01" placeholder="Qty" value={item.quantity} onChange={(e) => updateItem(index, 'quantity', Number(e.target.value))} className={inputClass} />
                      <input required type="number" min="0" step="0.01" placeholder="Unit price" value={item.unit_price} onChange={(e) => updateItem(index, 'unit_price', Number(e.target.value))} className={inputClass} />
                      <input required type="number" min="0" step="0.01" placeholder="GST %" value={item.tax_rate} onChange={(e) => updateItem(index, 'tax_rate', Number(e.target.value))} className={inputClass} />
                      <button type="button" disabled={form.items.length === 1} onClick={() => setForm({ ...form, items: form.items.filter((_, itemIndex) => itemIndex !== index) })} className="flex items-center justify-center rounded-lg border border-slate-700 text-slate-400 hover:border-rose-500/50 hover:text-rose-400 disabled:cursor-not-allowed disabled:opacity-30" aria-label="Remove line item"><Trash2 className="h-4 w-4" /></button>
                    </div>
                  ))}
                </div>
              </div>
              <label><span className={labelClass}>Notes</span><textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inputClass} /></label>
              <div className="flex flex-wrap justify-end gap-6 border-t border-slate-700 pt-4 text-sm"><span className="text-slate-400">Subtotal <strong className="ml-2 text-white">₹{subtotal.toFixed(2)}</strong></span><span className="text-slate-400">Tax <strong className="ml-2 text-white">₹{taxAmount.toFixed(2)}</strong></span><span className="text-slate-400">Total <strong className="ml-2 text-emerald-400">₹{totalAmount.toFixed(2)}</strong></span></div>
              <div className="flex justify-end gap-3 border-t border-slate-700 pt-5">
                <button type="button" onClick={() => setIsModalOpen(false)} disabled={saving} className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50">Cancel</button>
                <button type="submit" disabled={saving || vendors.length === 0} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50">{saving ? 'Saving...' : 'Create Purchase Order'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
