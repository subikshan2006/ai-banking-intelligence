import React, { useEffect, useState } from 'react';
import {
  Workflow,
  Cpu,
  Bot,
  Zap,
  Clock,
  CheckCircle,
  AlertCircle,
  Search,
  ArrowRight,
  Database
} from 'lucide-react';
import { api } from '../services/api';
import { Badge } from '../components/common/Badge';

export const WorkflowMonitorPage: React.FC = () => {
  const [agents, setAgents] = useState<any[]>([]);
  const [tools, setTools] = useState<any[]>([]);
  const [searchCorrId, setSearchCorrId] = useState('');
  const [traceLogs, setTraceLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgentsAndTools();
  }, []);

  const loadAgentsAndTools = async () => {
    try {
      setLoading(true);
      const [agRes, tRes] = await Promise.all([
        api.getAgentsStatus(),
        api.getTools()
      ]);
      setAgents(agRes.agents || []);
      setTools(tRes.tools || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchTrace = async () => {
    if (!searchCorrId.trim()) return;
    try {
      const logs = await api.getTrace(searchCorrId.trim());
      setTraceLogs(logs);
    } catch (err) {
      console.error(err);
      setTraceLogs([]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Workflow className="w-5 h-5 text-teal-400" />
          Multi-Agent Workflow & Topology Monitor
        </h1>
        <p className="text-xs text-slate-400">
          Supervisory DAG execution control plane, agent registry status, and real-time execution traces.
        </p>
      </div>

      {/* Workflow Architecture Visualizer */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-teal-400" />
            Supervisor Orchestrator Topology
          </h2>
          <span className="text-[11px] font-mono text-teal-400 bg-teal-950/60 border border-teal-800/40 px-2 py-0.5 rounded">
            DAG Sequential & Concurrent Dispatch
          </span>
        </div>

        {/* Visual Graph Diagram */}
        <div className="p-6 bg-navy-950 rounded-xl border border-slate-800/80 space-y-6">
          {/* Layer 1: Input */}
          <div className="flex items-center justify-center">
            <div className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-200 font-semibold shadow-md flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" /> Natural-Language Request
            </div>
          </div>

          <div className="flex justify-center">
            <div className="w-0.5 h-6 bg-slate-700"></div>
          </div>

          {/* Layer 2: Supervisor */}
          <div className="flex items-center justify-center">
            <div className="px-6 py-3 rounded-2xl bg-gradient-to-r from-teal-950 via-slate-900 to-teal-950 border border-teal-500/40 text-xs text-white font-bold shadow-lg shadow-teal-500/10 flex items-center gap-3">
              <Bot className="w-5 h-5 text-teal-400" />
              <div>
                <span className="block text-sm">SupervisorAgent</span>
                <span className="text-[10px] text-slate-400 font-normal">Intent Parser • Task Decomposition • Grounding</span>
              </div>
            </div>
          </div>

          <div className="flex justify-center">
            <div className="w-0.5 h-6 bg-slate-700"></div>
          </div>

          {/* Layer 3: Specialized Agents */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            {[
              { name: 'CustomerAgent', role: 'Profile & 360' },
              { name: 'TransactionAgent', role: 'Categories & Trends' },
              { name: 'FraudAgent', role: 'Anomaly & Rules' },
              { name: 'CreditAgent', role: 'EMI & DTI Math' },
              { name: 'ComplianceAgent', role: 'KYC & Checklists' },
              { name: 'InvestigationAgent', role: 'Consolidated 360' },
            ].map((ag) => (
              <div key={ag.name} className="p-3 bg-slate-900/90 border border-slate-800 rounded-xl text-center space-y-1">
                <span className="font-bold text-white text-xs block">{ag.name}</span>
                <span className="text-[10px] text-teal-400 block font-mono">{ag.role}</span>
              </div>
            ))}
          </div>

          <div className="flex justify-center">
            <div className="w-0.5 h-6 bg-slate-700"></div>
          </div>

          {/* Layer 4: Tool Registry */}
          <div className="flex items-center justify-center">
            <div className="px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-slate-300 font-medium flex items-center gap-2">
              <Database className="w-4 h-4 text-purple-400" /> 21 Registered Micro-Tools & SQLite WAL Ledger
            </div>
          </div>
        </div>
      </div>

      {/* Agents Registry Grid */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-white">Registered Autonomous Agents</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((ag) => (
            <div key={ag.name} className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-2 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm flex items-center gap-2">
                  <Bot className="w-4 h-4 text-teal-400" />
                  {ag.name}
                </span>
                <Badge label={ag.status} variant="verified" />
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{ag.description}</p>
              <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
                <span>Classification:</span>
                <span className="text-slate-300 font-mono">{ag.type}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Trace Search Inspector */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <Clock className="w-4 h-4 text-amber-400" />
          Correlation ID Execution Trace Inspector
        </h2>
        <div className="flex gap-2">
          <input
            type="text"
            value={searchCorrId}
            onChange={(e) => setSearchCorrId(e.target.value)}
            placeholder="Enter Correlation ID (e.g. REQ-APPR-001 or REQ-xxxxx)..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
          />
          <button
            onClick={handleSearchTrace}
            className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs rounded-xl transition flex items-center gap-1.5"
          >
            <Search className="w-3.5 h-3.5" /> Search Trace
          </button>
        </div>

        {traceLogs.length > 0 && (
          <div className="space-y-2 pt-2">
            <span className="text-xs font-semibold text-slate-400 block">Trace Events for {searchCorrId}</span>
            <div className="space-y-2">
              {traceLogs.map((log) => (
                <div key={log.id} className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl text-xs space-y-1 font-mono">
                  <div className="flex justify-between items-center text-teal-400 font-bold">
                    <span>[{log.actor}] {log.event_type}</span>
                    <span className="text-slate-500 text-[11px]">{log.duration_ms}ms</span>
                  </div>
                  {log.tool_name && <div className="text-slate-300">Tool: {log.tool_name}</div>}
                  <div className="text-[10px] text-slate-500">{log.timestamp}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
