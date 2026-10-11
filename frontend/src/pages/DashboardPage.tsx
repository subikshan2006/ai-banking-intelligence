import React, { useEffect, useState } from 'react';
import {
  Users,
  CreditCard,
  TrendingUp,
  ShieldAlert,
  Clock,
  Briefcase,
  Activity,
  Sparkles,
  ArrowRight,
  AlertTriangle
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';
import { MetricCard } from '../components/common/MetricCard';
import { Badge } from '../components/common/Badge';
import { api } from '../services/api';
import { DashboardMetrics } from '../types';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
  onGenerateDemoTx: () => void;
}

const COLORS = ['#14B8A6', '#0EA5E9', '#F59E0B', '#8B5CF6', '#EC4899', '#10B981'];

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate, onGenerateDemoTx }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const summary = await api.getDashboardSummary();
      setData(summary);
    } catch (err) {
      console.error('Error loading dashboard summary:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-slate-400 text-sm">
        <Activity className="w-5 h-5 animate-spin mr-2 text-teal-400" />
        Loading real-time executive dashboard...
      </div>
    );
  }

  const metrics: DashboardMetrics = data.metrics;
  const recentAlerts = data.recent_alerts || [];
  const categorySpending = data.category_spending || [];

  const riskPieData = [
    { name: 'Low Risk', value: data.risk_distribution?.LOW || 0, color: '#10B981' },
    { name: 'Medium Risk', value: data.risk_distribution?.MEDIUM || 0, color: '#F59E0B' },
    { name: 'High Risk', value: data.risk_distribution?.HIGH || 0, color: '#F43F5E' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner and Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-navy-900 via-navy-800 to-slate-900 border border-slate-800 p-6 rounded-2xl shadow-md">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            Operations Command Center
            <span className="text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded-full">
              Live Core
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time synthetic banking environment monitored by autonomous multi-agent supervisory controls.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('assistant')}
            className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-navy-950 font-semibold text-xs rounded-xl transition flex items-center gap-2 shadow-lg shadow-teal-500/20"
          >
            <Sparkles className="w-4 h-4" />
            Launch AI Assistant
          </button>
          <button
            onClick={onGenerateDemoTx}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium text-xs rounded-xl transition flex items-center gap-1.5"
          >
            Trigger Event
          </button>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Synthetic Customers"
          value={metrics.total_customers}
          subtitle="All profiles KYC grounded"
          icon={Users}
          accentColor="blue"
        />
        <MetricCard
          title="Total Ledger Volume"
          value={`₹${(metrics.total_transaction_volume / 100000).toFixed(1)}L`}
          subtitle={`${metrics.total_transactions_count} total transactions`}
          icon={TrendingUp}
          accentColor="teal"
        />
        <MetricCard
          title="Potential Fraud Alerts"
          value={metrics.open_fraud_alerts}
          subtitle={`${metrics.total_fraud_alerts} cumulative analyzed`}
          icon={ShieldAlert}
          accentColor="rose"
          trend="Review Req"
          trendPositive={false}
        />
        <MetricCard
          title="Pending Approvals"
          value={metrics.pending_approvals}
          subtitle="Human-in-the-loop queue"
          icon={Clock}
          accentColor="amber"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Spending Bar Chart */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Expenditure by Commercial Category</h3>
              <p className="text-xs text-slate-400">Aggregated from authoritative core debit transactions</p>
            </div>
            <button
              onClick={() => onNavigate('customers')}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
            >
              Explore accounts <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categorySpending} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="category" stroke="#64748B" fontSize={11} interval={0} angle={-25} textAnchor="end" />
                <YAxis stroke="#64748B" fontSize={11} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B1528', borderColor: '#1E293B', borderRadius: 8, fontSize: 12 }}
                  formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Total Spent']}
                />
                <Bar dataKey="amount" fill="#14B8A6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution Pie */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white mb-1">Fraud Risk Severity Distribution</h3>
            <p className="text-xs text-slate-400 mb-4">Isolation Forest ML + Rule Engine detections</p>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {riskPieData.map((entry, idx) => (
                      <Cell key={`cell-${idx}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0B1528', borderColor: '#1E293B', borderRadius: 8, fontSize: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-center text-xs">
            {riskPieData.map((item) => (
              <div key={item.name}>
                <span className="block text-[11px] text-slate-400">{item.name.replace(' Risk', '')}</span>
                <span className="font-bold text-white text-sm" style={{ color: item.color }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Alerts Feed & Agent Activity Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              Recent Fraud & Risk Alerts
            </h3>
            <button
              onClick={() => onNavigate('fraud')}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-2.5">
            {recentAlerts.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No active fraud alerts detected.</p>
            ) : (
              recentAlerts.map((alert: any) => (
                <div
                  key={alert.id}
                  onClick={() => onNavigate('fraud')}
                  className="p-3 bg-slate-950/60 border border-slate-800/70 hover:border-slate-700 rounded-xl flex items-center justify-between transition cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-rose-950/60 border border-rose-800/30 text-rose-400">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-white">{alert.transaction_id}</span>
                        <span className="text-[11px] text-slate-400">({alert.customer_id})</span>
                      </div>
                      <span className="text-[11px] text-slate-500">Risk Score: {alert.risk_score}/100</span>
                    </div>
                  </div>
                  <Badge label={alert.risk_level} variant={alert.risk_level} />
                </div>
              ))
            )}
          </div>
        </div>

        {/* Operational Multi-Agent Coordination Box */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-teal-400" />
                Active Multi-Agent Control Plane
              </h3>
              <button
                onClick={() => onNavigate('workflow')}
                className="text-xs text-teal-400 hover:text-teal-300 font-medium flex items-center gap-1"
              >
                Inspect traces <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              The Supervisor Agent autonomously routes requests across 7 specialized banking agents with DAG dependency planning, tool permissions, and deterministic fallback support.
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] text-slate-400 block">Agent Executions</span>
                <span className="font-bold text-white text-base">{metrics.agent_executions_count}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-[11px] text-slate-400 block">Active Micro-Tools</span>
                <span className="font-bold text-teal-400 text-base">21 Registered</span>
              </div>
            </div>
          </div>
          <div className="pt-4 mt-4 border-t border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-400">Automated Evaluation Suite</span>
            <button
              onClick={() => onNavigate('evaluation')}
              className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-teal-300 rounded-lg font-medium transition"
            >
              Run Benchmark
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
