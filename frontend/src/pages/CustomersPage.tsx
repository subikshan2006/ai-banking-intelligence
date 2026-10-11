import React, { useEffect, useState } from 'react';
import {
  Search,
  Users,
  CreditCard,
  TrendingDown,
  ShieldCheck,
  Building,
  MapPin,
  Calendar,
  X,
  ExternalLink,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { Customer } from '../types';
import { Badge } from '../components/common/Badge';

interface CustomersPageProps {
  onInvestigateCustomer: (customerId: string) => void;
}

export const CustomersPage: React.FC<CustomersPageProps> = ({ onInvestigateCustomer }) => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedCust, setSelectedCust] = useState<any | null>(null);
  const [drawerLoading, setDrawerLoading] = useState(false);

  useEffect(() => {
    loadCustomers();
  }, [search]);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      const res = await api.getCustomers(search, 30);
      setCustomers(res.customers);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCustomer = async (cust: Customer) => {
    try {
      setDrawerLoading(true);
      const details = await api.getCustomerDetails(cust.id);
      setSelectedCust(details);
    } catch (err) {
      console.error(err);
    } finally {
      setDrawerLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-teal-400" />
            Customer 360 Explorer
          </h1>
          <p className="text-xs text-slate-400">Searchable repository of synthetic customer accounts and KYC profiles.</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID, name, or city..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
          />
        </div>
      </div>

      {/* Customers Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Customer</th>
                <th className="px-5 py-3">Location & Employer</th>
                <th className="px-5 py-3">Monthly Income</th>
                <th className="px-5 py-3">KYC Status</th>
                <th className="px-5 py-3">Risk Rating</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-500">Loading customers...</td>
                </tr>
              ) : customers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-slate-500">No customers found matching search.</td>
                </tr>
              ) : (
                customers.map((c) => (
                  <tr
                    key={c.id}
                    className="hover:bg-slate-800/40 transition cursor-pointer"
                    onClick={() => handleSelectCustomer(c)}
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-white">{c.name}</div>
                      <div className="text-[11px] text-teal-400 font-mono">{c.id}</div>
                    </td>
                    <td className="px-5 py-3.5 text-slate-300">
                      <div>{c.employer}</div>
                      <div className="text-[11px] text-slate-500">{c.city}</div>
                    </td>
                    <td className="px-5 py-3.5 text-white font-medium">
                      ₹{c.monthly_income.toLocaleString()}
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge label={c.kyc_status} variant={c.kyc_status} />
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge label={c.risk_rating} variant={c.risk_rating} />
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectCustomer(c);
                        }}
                        className="text-teal-400 hover:text-teal-300 font-medium text-xs px-2.5 py-1 rounded-lg bg-teal-950/40 border border-teal-800/30 hover:bg-teal-900/40 transition"
                      >
                        Inspect 360
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Customer 360 Detail Drawer / Modal */}
      {selectedCust && (
        <div className="fixed inset-y-0 right-0 w-full max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl z-50 p-6 overflow-y-auto space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h2 className="text-base font-bold text-white">{selectedCust.customer.name}</h2>
              <span className="text-xs font-mono text-teal-400">{selectedCust.customer.id}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onInvestigateCustomer(selectedCust.customer.id)}
                className="px-3 py-1.5 bg-teal-500 hover:bg-teal-400 text-navy-950 text-xs font-bold rounded-lg flex items-center gap-1.5 transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                AI 360 Investigation
              </button>
              <button
                onClick={() => setSelectedCust(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Profile Overview */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-slate-500 block">Employer</span>
              <span className="text-white font-medium">{selectedCust.customer.employer}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-slate-500 block">City</span>
              <span className="text-white font-medium">{selectedCust.customer.city}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-slate-500 block">Monthly Income</span>
              <span className="text-white font-bold">₹{selectedCust.customer.monthly_income.toLocaleString()}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-slate-500 block">KYC Status</span>
              <Badge label={selectedCust.customer.kyc_status} variant={selectedCust.customer.kyc_status} />
            </div>
          </div>

          {/* Associated Accounts */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Associated Bank Accounts
            </h3>
            <div className="space-y-2">
              {selectedCust.accounts.map((acc: any) => (
                <div key={acc.id} className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-white">{acc.account_type}</span>
                    <span className="text-slate-500 block font-mono text-[11px]">{acc.masked_account_number}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-teal-400 text-sm">₹{acc.balance.toLocaleString()}</span>
                    <span className="text-[10px] text-slate-500 block">{acc.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Spending Summary */}
          {selectedCust.spending_summary && (
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Monthly Spending Distribution
              </h3>
              <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2 text-xs">
                <div className="flex justify-between text-slate-400 pb-2 border-b border-slate-800">
                  <span>Total Inflow: <b className="text-white">₹{selectedCust.spending_summary.total_inflow.toLocaleString()}</b></span>
                  <span>Total Outflow: <b className="text-rose-400">₹{selectedCust.spending_summary.total_outflow.toLocaleString()}</b></span>
                </div>
                <div className="space-y-1.5 pt-1">
                  {selectedCust.spending_summary.categories.slice(0, 4).map((c: any) => (
                    <div key={c.category} className="flex justify-between items-center text-[11px]">
                      <span className="text-slate-300">{c.category}</span>
                      <span className="text-slate-400 font-mono">₹{c.total_amount.toLocaleString()} ({c.percentage}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Recent Activity */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Recent Transactions
            </h3>
            <div className="space-y-1.5">
              {selectedCust.recent_transactions.slice(0, 5).map((t: any) => (
                <div key={t.id} className="p-2.5 bg-slate-950/40 border border-slate-800/80 rounded-lg flex items-center justify-between text-xs">
                  <div>
                    <span className="text-white font-medium">{t.merchant_name}</span>
                    <span className="text-[10px] text-slate-500 block">{t.category} • {t.status}</span>
                  </div>
                  <div className="text-right">
                    <span className={`font-semibold ${t.txn_type === 'CREDIT' ? 'text-emerald-400' : 'text-slate-200'}`}>
                      {t.txn_type === 'CREDIT' ? '+' : '-'}₹{t.amount.toLocaleString()}
                    </span>
                    {t.is_flagged && <span className="text-[10px] text-rose-400 block font-semibold">Flagged</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
