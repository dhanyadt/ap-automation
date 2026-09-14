import React, { useEffect, useState } from 'react';
import { PackageCheck, Plus, X } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

type POItem = {
  id: string;
  description: string;
  quantity: number | string;
};

type GRNItem = {
  po_item: string;
  description: string;
  ordered_quantity: number;
  received_quantity: number;
  accepted_quantity: number;
  rejected_quantity: number;
  remarks: string;
};

type GRNForm = {
  grn_number: string;
  purchase_order: string;
  status: string;
  received_date: string;
  delivery_challan_number: string;
  received_by: string;
  notes: string;
  items: GRNItem[];
};

const initialForm: GRNForm = {
  grn_number: '',
  purchase_order: '',
  status: 'RECEIVED',
  received_date: new Date().toISOString().slice(0, 10),
  delivery_challan_number: '',
  received_by: '',
  notes: '',
  items: [],
};

const inputClass = 'w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500';
const labelClass = 'mb-1.5 block text-xs font-medium text-slate-300';

const formatApiError = (error: any): string => {
  const data = error?.response?.data;
  if (!data) return 'Unable to create goods receipt. Please try again.';
  if (typeof data === 'string') return data;
  return Object.entries(data).map(([field, value]) => {
    const message = Array.isArray(value) ? value.join(', ') : String(value);
    return `${field === 'non_field_errors' ? 'Error' : field}: ${message}`;
  }).join(' | ');
};

export const GoodsReceipts: React.FC = () => {
  const { user } = useAuth();
  const [grns, setGrns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState<GRNForm>(initialForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const canCreate = user?.role === 'AP_CLERK' || user?.role === 'ADMIN';

  const fetchGRNs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/goods-receipts/');
      setGrns(res.data?.results || []);
    } catch (err) {
      console.error('Failed to load GRNs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGRNs();
  }, []);

  const openModal = async () => {
    setForm(initialForm);
    setFormError('');
    setIsModalOpen(true);
    try {
      const response = await api.get('/purchase-orders/?status=ISSUED');
      setPurchaseOrders(response.data?.results || []);
    } catch (error) {
      setFormError('Unable to load issued purchase orders. Please close and try again.');
    }
  };

  const selectPurchaseOrder = async (purchaseOrderId: string) => {
    setForm((current) => ({ ...current, purchase_order: purchaseOrderId, items: [] }));
    if (!purchaseOrderId) return;
    try {
      const response = await api.get(`/purchase-orders/${purchaseOrderId}/`);
      const items: POItem[] = response.data?.items || [];
      setForm((current) => ({
        ...current,
        items: items.map((item) => ({
          po_item: item.id,
          description: item.description,
          ordered_quantity: Number(item.quantity),
          received_quantity: 0,
          accepted_quantity: 0,
          rejected_quantity: 0,
          remarks: '',
        })),
      }));
    } catch (error) {
      setFormError('Unable to load purchase order items. Please try selecting the PO again.');
    }
  };

  const updateItem = (index: number, field: keyof GRNItem, value: string | number) => {
    setForm((current) => ({
      ...current,
      items: current.items.map((item, itemIndex) => {
        if (itemIndex !== index) return item;
        const updated = { ...item, [field]: value };
        if (field === 'received_quantity') {
          updated.accepted_quantity = Number(value);
          updated.rejected_quantity = 0;
        }
        return updated;
      }),
    }));
  };

  const submitGRN = async (event: React.FormEvent) => {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    setFormError('');
    try {
      await api.post('/goods-receipts/', {
        grn_number: form.grn_number,
        purchase_order: form.purchase_order,
        status: form.status,
        received_date: form.received_date,
        delivery_challan_number: form.delivery_challan_number,
        received_by: form.received_by,
        notes: form.notes,
        items: form.items.map((item) => ({
          po_item: item.po_item,
          received_quantity: item.received_quantity,
          accepted_quantity: item.accepted_quantity,
          rejected_quantity: item.rejected_quantity,
          remarks: item.remarks,
        })),
      });
      setIsModalOpen(false);
      await fetchGRNs();
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
          <h1 className="text-2xl font-bold text-white tracking-tight">Goods Receipt Notes (GRN)</h1>
          <p className="text-sm text-slate-400">Warehouse deliveries and inspection receipts required for 3-way matching</p>
        </div>
        {canCreate && (
          <button type="button" onClick={openModal} className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-900/20 hover:bg-blue-500">
            <Plus className="h-4 w-4" /> Add GRN
          </button>
        )}
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

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-2xl border border-slate-700 bg-slate-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-700 px-6 py-4">
              <div>
                <h2 className="text-lg font-bold text-white">Add Goods Receipt Note</h2>
                <p className="mt-1 text-xs text-slate-400">Record delivered quantities against an issued purchase order.</p>
              </div>
              <button type="button" onClick={() => !saving && setIsModalOpen(false)} disabled={saving} className="rounded-lg p-2 text-slate-400 hover:bg-slate-700 hover:text-white disabled:opacity-50" aria-label="Close modal">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={submitGRN} className="space-y-5 p-6">
              {formError && <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert">{formError}</div>}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <label><span className={labelClass}>GRN number *</span><input required value={form.grn_number} onChange={(e) => setForm({ ...form, grn_number: e.target.value })} className={inputClass} /></label>
                <label><span className={labelClass}>Purchase order *</span><select required value={form.purchase_order} onChange={(e) => selectPurchaseOrder(e.target.value)} className={inputClass}><option value="">Select issued PO</option>{purchaseOrders.map((po) => <option key={po.id} value={po.id}>{po.po_number} - {po.vendor_name}</option>)}</select></label>
                <label><span className={labelClass}>Status</span><select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className={inputClass}><option value="RECEIVED">Received</option><option value="INSPECTED">Inspected</option><option value="ACCEPTED">Accepted</option><option value="REJECTED">Rejected</option></select></label>
                <label><span className={labelClass}>Received date *</span><input required type="date" value={form.received_date} onChange={(e) => setForm({ ...form, received_date: e.target.value })} className={inputClass} /></label>
                <label><span className={labelClass}>Delivery challan number</span><input value={form.delivery_challan_number} onChange={(e) => setForm({ ...form, delivery_challan_number: e.target.value })} className={inputClass} /></label>
                <label><span className={labelClass}>Received by</span><input value={form.received_by} onChange={(e) => setForm({ ...form, received_by: e.target.value })} className={inputClass} /></label>
              </div>

              <div>
                <h3 className="mb-3 text-sm font-semibold text-white">Received items</h3>
                {!form.purchase_order ? (
                  <div className="rounded-xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">Select a purchase order to load its items.</div>
                ) : form.items.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-500">This purchase order has no line items.</div>
                ) : (
                  <div className="space-y-3">
                    {form.items.map((item, index) => (
                      <div key={item.po_item} className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
                        <div className="mb-3 flex items-center justify-between">
                          <span className="text-sm font-medium text-white">{item.description}</span>
                          <span className="text-xs text-slate-400">Ordered: {item.ordered_quantity}</span>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                          <label><span className={labelClass}>Received quantity</span><input required type="number" min="0" step="0.01" value={item.received_quantity} onChange={(e) => updateItem(index, 'received_quantity', Number(e.target.value))} className={inputClass} /></label>
                          <label><span className={labelClass}>Accepted quantity</span><input required type="number" min="0" step="0.01" value={item.accepted_quantity} onChange={(e) => updateItem(index, 'accepted_quantity', Number(e.target.value))} className={inputClass} /></label>
                          <label><span className={labelClass}>Rejected quantity</span><input required type="number" min="0" step="0.01" value={item.rejected_quantity} onChange={(e) => updateItem(index, 'rejected_quantity', Number(e.target.value))} className={inputClass} /></label>
                          <label><span className={labelClass}>Remarks</span><input value={item.remarks} onChange={(e) => updateItem(index, 'remarks', e.target.value)} className={inputClass} /></label>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <label><span className={labelClass}>Notes</span><textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inputClass} /></label>
              <div className="flex justify-end gap-3 border-t border-slate-700 pt-5">
                <button type="button" onClick={() => setIsModalOpen(false)} disabled={saving} className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:opacity-50">Cancel</button>
                <button type="submit" disabled={saving || !form.purchase_order || form.items.length === 0} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50">{saving ? 'Saving...' : 'Create GRN'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
