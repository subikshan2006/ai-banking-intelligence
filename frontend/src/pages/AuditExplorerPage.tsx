import React, { useEffect, useState } from 'react';
import {
  History,
  Filter,
  Search,
  RefreshCw,
  FileCode,
  ShieldCheck,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { AuditLog } from '../types';
import { Badge } from '../components/common/Badge';

export const AuditExplorerPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actorFilter, setActorFilter] = useState('');
  const [corrFilter, setCorrFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  useEffect(() => {
    loadAuditLogs();
  }, [actorFilter]);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const res = await api.getAuditLogs(corrFilter || undefined, actorFilter || undefined, 50);
      setLogs(res.logs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadAuditLogs();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-teal-400" />
            Append-Only Audit Explorer
          </h1>
          <p className="text-xs text-slate-400">
            Immutable operation log capturing every agent invocation, tool call, approval decision, and PII-masked payload.
          </p>
        </div>
        <button
          onClick={loadAuditLogs}
          className="p-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white rounded-xl transition flex items-center gap-1.5 text-xs font-medium"
        >
          <RefreshCw className="w-4 h-4" /> Refresh Audit Trail
        </button>
      </div>

      {/* Filter Bar */}
      <form onSubmit={handleSearch} className="flex flex-wrap gap-3 bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            value={corrFilter}
            onChange={(e) => setCorrFilter(e.target.value)}
            placeholder="Filter by Correlation ID..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
          />
        </div>
        <select
          value={actorFilter}
          onChange={(e) => setActorFilter(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
        >
          <option value="">All Actors</option>
          <option value="SupervisorAgent">SupervisorAgent</option>
          <option value="CustomerAgent">CustomerAgent</option>
          <option value="FraudAgent">FraudAgent</option>
          <option value="CreditAgent">CreditAgent</option>
          <option value="ToolRegistry">ToolRegistry</option>
          <option value="compliance_manager">compliance_manager</option>
        </select>
        <button
          type="submit"
          className="px-4 py-1.5 bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs rounded-lg transition"
        >
          Filter
        </button>
      </form>

      {/* Audit Logs Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Correlation ID</th>
                <th className="px-5 py-3">Actor</th>
                <th className="px-5 py-3">Event Type</th>
                <th className="px-5 py-3">Tool Name</th>
                <th className="px-5 py-3">Latency</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-500 font-sans">Loading audit records...</td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-500 font-sans">No audit logs found.</td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr
                    key={log.id}
                    className="hover:bg-slate-800/40 transition cursor-pointer"
                    onClick={() => setSelectedLog(log)}
                  >
                    <td className="px-5 py-3.5 text-slate-400 text-[11px] whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-5 py-3.5 text-teal-400 font-semibold">{log.correlation_id}</td>
                    <td className="px-5 py-3.5 text-white font-medium">{log.actor}</td>
                    <td className="px-5 py-3.5 text-amber-300 font-semibold">{log.event_type}</td>
                    <td className="px-5 py-3.5 text-slate-300">{log.tool_name || '-'}</td>
                    <td className="px-5 py-3.5 text-slate-400">{log.duration_ms}ms</td>
                    <td className="px-5 py-3.5">
                      <Badge label={log.status} variant={log.status === 'SUCCESS' ? 'verified' : (log.status === 'ERROR' ? 'high' : 'warning')} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Log Detail Viewer */}
      {selectedLog && (
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs font-mono">
          <div className="flex items-center justify-between text-white font-bold border-b border-slate-800 pb-2">
            <span>Audit Entry #{selectedLog.id} — {selectedLog.event_type}</span>
            <span className="text-teal-400">{selectedLog.correlation_id}</span>
          </div>
          <div className="text-slate-400 text-[11px]">Actor: {selectedLog.actor} | Duration: {selectedLog.duration_ms}ms | Timestamp: {selectedLog.timestamp}</div>
          <pre className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-[11px] text-teal-300 overflow-x-auto">
            {JSON.stringify(JSON.parse(selectedLog.details || '{}'), null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
