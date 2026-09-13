import React, { useEffect, useState } from 'react';
import { Building2, Search, CheckCircle2, XCircle, Plus, X } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

type VendorForm = {
  name: string;
  code: string;
  gstin: string;
  pan: string;
  email: string;
  phone: string;
  address_line1: string;
  city: string;
  state: string;
  pincode: string;
  status: string;
  msme_registered: boolean;
  payment_terms_days: number;
};

const initialForm: VendorForm = {
  name: '',
  code: '',
  gstin: '',
  pan: '',
  email: '',
  phone: '',
  address_line1: '',
  city: '',
  state: '',
  pincode: '',
  status: 'ACTIVE',
  msme_registered: false,
  payment_terms_days: 30,
};

const formatApiError = (error: any): string => {
  const data = error?.response?.data;
  if (!data) return 'Unable to create vendor. Please try again.';
  if (typeof data === 'string') return data;
  return Object.entries(data)
    .map(([field, value]) => {
      const messages = Array.isArray(value) ? value.join(', ') : String(value);
      return `${field === 'non_field_errors' ? 'Error' : field}: ${messages}`;
    })
    .join(' | ');
};

export const Vendors: React.FC = () => {
  const { user } = useAuth();
  const [vendors, setVendors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState<VendorForm>(initialForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const canAddVendor = user?.role === 'AP_CLERK' || user?.role === 'ADMIN';

  const fetchVendors = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/vendors/?search=${searchTerm}`);
      setVendors(res.data?.results || []);
    } catch (err) {
      console.error('Failed to load vendors:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, [searchTerm]);

  const openModal = () => {
    setForm(initialForm);
    setFormError('');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    if (!saving) setIsModalOpen(false);
  };

  const submitVendor = async (event: React.FormEvent) => {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    setFormError('');
    try {
      await api.post('/vendors/', form);
      setIsModalOpen(false);
      setForm(initialForm);
      await fetchVendors();
    } catch (error) {
      setFormError(formatApiError(error));
    } finally {
      setSaving(false);
    }
  };

  const updateField = <K extends keyof VendorForm>(field: K, value: VendorForm[K]) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Vendor Master Directory</h1>
          <p className="text-sm text-slate-400">Manage registered vendor partners, GSTIN compliance, and masked bank rails</p>
        </div>
        {canAddVendor && (
          <button
            type="button"
            onClick={openModal}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-900/20 transition-colors hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <Plus className="h-4 w-4" />
            Add Vendor
          </button>
        )}
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search vendors by name, code, GSTIN, city..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <span className="text-xs text-slate-400">{vendors.length} vendors active</span>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-850/50 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="p-3.5 pl-5">Vendor Code</th>
                <th className="p-3.5">Company Name</th>
                <th className="p-3.5">GSTIN / PAN</th>
                <th className="p-3.5">Location</th>
                <th className="p-3.5">Bank Account (Masked)</th>
                <th className="p-3.5">Credit Terms</th>
                <th className="p-3.5 pr-5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    Loading vendors...
                  </td>
                </tr>
              ) : vendors.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No vendors registered yet.
                  </td>
                </tr>
              ) : (
                vendors.map((v) => {
                  const primaryBank = v.bank_accounts?.find((b: any) => b.is_primary) || v.bank_accounts?.[0];
                  return (
                    <tr key={v.id} className="hover:bg-slate-750/30 transition-colors">
                      <td className="p-3.5 pl-5 font-mono text-blue-400 font-semibold">{v.code}</td>
                      <td className="p-3.5 font-medium text-white">{v.name}</td>
                      <td className="p-3.5 font-mono text-slate-300">
                        <div>{v.gstin || '—'}</div>
                        <div className="text-[10px] text-slate-500">{v.pan || ''}</div>
                      </td>
                      <td className="p-3.5 text-slate-400">
                        {v.city ? `${v.city}, ${v.state}` : '—'}
                      </td>
                      <td className="p-3.5">
                        {primaryBank ? (
                          <div>
                            <span className="font-mono text-slate-200">{primaryBank.masked_account_number}</span>
                            <span className="text-[10px] text-slate-400 block">{primaryBank.bank_name}</span>
                          </div>
                        ) : (
                          <span className="text-slate-500 italic">No bank recorded</span>
                        )}
                      </td>
                      <td className="p-3.5 text-slate-300">{v.payment_terms_days} days</td>
                      <td className="p-3.5 pr-5">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            v.status === 'ACTIVE'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          }`}
                        >
                          {v.status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-slate-700 bg-slate-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-700 px-6 py-4">
              <div>
                <h2 className="text-lg font-bold text-white">Add Vendor</h2>
                <p className="mt-1 text-xs text-slate-400">Register a vendor partner in the master directory.</p>
              </div>
              <button type="button" onClick={closeModal} disabled={saving} className="rounded-lg p-2 text-slate-400 hover:bg-slate-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-50" aria-label="Close modal">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={submitVendor} className="space-y-5 p-6">
              {formError && (
                <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300" role="alert">
                  {formError}
                </div>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                {([
                  ['name', 'Vendor name', true],
                  ['code', 'Vendor code', true],
                  ['gstin', 'GSTIN', false],
                  ['pan', 'PAN', false],
                  ['email', 'Email', false],
                  ['phone', 'Phone', false],
                  ['address_line1', 'Address', false],
                  ['city', 'City', false],
                  ['state', 'State', false],
                  ['pincode', 'Pincode', false],
                ] as [keyof VendorForm, string, boolean][]).map(([field, label, required]) => (
                  <label key={field} className={field === 'address_line1' ? 'sm:col-span-2' : ''}>
                    <span className="mb-1.5 block text-xs font-medium text-slate-300">{label}{required && <span className="text-rose-400"> *</span>}</span>
                    <input
                      type={field === 'email' ? 'email' : 'text'}
                      value={form[field] as string}
                      onChange={(event) => updateField(field, event.target.value)}
                      required={required}
                      className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </label>
                ))}

                <label>
                  <span className="mb-1.5 block text-xs font-medium text-slate-300">Status</span>
                  <select value={form.status} onChange={(event) => updateField('status', event.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500">
                    <option value="ACTIVE">Active</option>
                    <option value="INACTIVE">Inactive</option>
                    <option value="BLOCKED">Blocked</option>
                    <option value="DRAFT">Draft</option>
                    <option value="PENDING_REVIEW">Pending review</option>
                  </select>
                </label>
                <label>
                  <span className="mb-1.5 block text-xs font-medium text-slate-300">Payment terms (days)</span>
                  <input type="number" min="0" value={form.payment_terms_days} onChange={(event) => updateField('payment_terms_days', Number(event.target.value))} className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500" />
                </label>
              </div>

              <label className="flex items-center gap-3 text-sm text-slate-300">
                <input type="checkbox" checked={form.msme_registered} onChange={(event) => updateField('msme_registered', event.target.checked)} className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-blue-600 focus:ring-blue-500" />
                MSME registered
              </label>

              <div className="flex justify-end gap-3 border-t border-slate-700 pt-5">
                <button type="button" onClick={closeModal} disabled={saving} className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50">
                  Cancel
                </button>
                <button type="submit" disabled={saving} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50">
                  {saving ? 'Saving...' : 'Create Vendor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
