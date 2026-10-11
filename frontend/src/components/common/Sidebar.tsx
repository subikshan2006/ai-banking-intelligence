import React from 'react';
import {
  LayoutDashboard,
  Bot,
  Users,
  ShieldAlert,
  FileSpreadsheet,
  Workflow,
  CheckCircle,
  BookOpen,
  History,
  Gauge
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingApprovalsCount: number;
  openAlertsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  pendingApprovalsCount,
  openAlertsCount
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: LayoutDashboard },
    { id: 'assistant', label: 'AI Assistant', icon: Bot, badge: 'Agentic' },
    { id: 'customers', label: 'Customer Explorer', icon: Users },
    { id: 'fraud', label: 'Fraud & Risk Center', icon: ShieldAlert, count: openAlertsCount, countColor: 'bg-rose-500' },
    { id: 'loans', label: 'Loan Assessment', icon: FileSpreadsheet },
    { id: 'workflow', label: 'Multi-Agent Monitor', icon: Workflow },
    { id: 'approvals', label: 'Approval Center', icon: CheckCircle, count: pendingApprovalsCount, countColor: 'bg-amber-500' },
    { id: 'knowledge', label: 'Policy Knowledge', icon: BookOpen },
    { id: 'audit', label: 'Audit Explorer', icon: History },
    { id: 'evaluation', label: 'Evaluation & Benchmarks', icon: Gauge },
  ];

  return (
    <aside className="w-64 bg-navy-950 border-r border-slate-800/80 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4 flex-1 space-y-1">
        <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 px-3 py-2">
          Banking Modules
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition group ${
                isActive
                  ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 transition ${isActive ? 'text-teal-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-semibold bg-teal-500/20 text-teal-300 px-1.5 py-0.5 rounded border border-teal-500/30">
                  {item.badge}
                </span>
              )}
              {item.count !== undefined && item.count > 0 && (
                <span className={`text-[10px] font-bold text-white px-1.5 py-0.2 rounded-full ${item.countColor}`}>
                  {item.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer System Info */}
      <div className="p-4 border-t border-slate-900 bg-slate-950/40 text-[11px] text-slate-500 space-y-1">
        <div className="flex justify-between">
          <span>Engine:</span>
          <span className="text-slate-400 font-mono">FastAPI + SQLite WAL</span>
        </div>
        <div className="flex justify-between">
          <span>Control Plane:</span>
          <span className="text-teal-400 font-medium">Supervisor DAG</span>
        </div>
      </div>
    </aside>
  );
};
