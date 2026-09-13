import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Building2,
  ShoppingCart,
  PackageCheck,
  ShieldAlert,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  Clock,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [counts, setCounts] = useState({
    invoices: 0,
    vendors: 0,
    pos: 0,
    grns: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCounts = async () => {
      try {
        const [invRes, vendRes, poRes, grnRes] = await Promise.all([
          api.get('/invoices/'),
          api.get('/vendors/'),
          api.get('/purchase-orders/'),
          api.get('/goods-receipts/'),
        ]);
        setCounts({
          invoices: invRes.data?.count || 0,
          vendors: vendRes.data?.count || 0,
          pos: poRes.data?.count || 0,
          grns: grnRes.data?.count || 0,
        });
      } catch (err) {
        console.error('Failed to load entity counts:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCounts();
  }, []);

  const stats = [
    { label: 'Active Invoices', value: counts.invoices, icon: FileText, path: '/invoices', color: 'blue' },
    { label: 'Registered Vendors', value: counts.vendors, icon: Building2, path: '/vendors', color: 'indigo' },
    { label: 'Purchase Orders', value: counts.pos, icon: ShoppingCart, path: '/purchase-orders', color: 'purple' },
    { label: 'Goods Receipts (GRN)', value: counts.grns, icon: PackageCheck, path: '/goods-receipts', color: 'emerald' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-900/40 via-slate-800 to-indigo-900/30 border border-slate-700/60 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Phase 2 Core API Foundation
              </span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Welcome back, {user?.first_name || user?.email}!
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Logged in as <span className="font-semibold text-slate-200">{user?.role}</span> in{' '}
              <span className="font-semibold text-slate-200">{user?.department || 'Operations'}</span>
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to="/invoices"
              className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-4 py-2.5 rounded-xl transition-colors shadow-lg shadow-blue-600/20"
            >
              <span>Manage Invoices</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((st) => {
          const Icon = st.icon;
          return (
            <Link
              key={st.label}
              to={st.path}
              className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 hover:border-slate-600 rounded-2xl p-5 transition-all duration-200 shadow-sm group"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-400">{st.label}</span>
                <div className="w-8 h-8 rounded-lg bg-slate-700/50 flex items-center justify-center text-slate-300 group-hover:text-white transition-colors">
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-bold text-white">
                {loading ? '...' : st.value}
              </div>
              <div className="mt-2 text-[11px] text-slate-400 flex items-center group-hover:text-blue-400 transition-colors">
                <span>View records</span>
                <ArrowRight className="w-3 h-3 ml-1" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* Phase Roadmap Note */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-2 flex items-center">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2" /> Current Phase Status: Core Domain APIs Active
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed mb-4">
          All core entities (Vendors, Bank Accounts, Purchase Orders, Goods Receipts, Invoices, and Audit Trail) are connected
          to PostgreSQL/SQLite database models with RBAC permissions and JWT authentication.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 font-medium">Phase 1 & 2 Completed</span>
            <span className="text-emerald-400 font-semibold">✓ Auth, RBAC & Core CRUD</span>
          </div>
          <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 font-medium">Phase 3 Up Next</span>
            <span className="text-blue-400 font-semibold">OCR, Validations, 3-Way Match & Approvals</span>
          </div>
          <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 font-medium">Interactive API Docs</span>
            <a href="http://localhost:8000/api/docs/" target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline font-semibold">
              Open Swagger UI ↗
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
