import React, { useEffect, useState } from 'react';
import {
  CheckCircle,
  XCircle,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Lock,
  FileCode,
  UserCheck
} from 'lucide-react';
import { api } from '../services/api';
import { ApprovalRequest } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

interface ApprovalCenterPageProps {
  demoRole: string;
}

export const ApprovalCenterPage: React.FC<ApprovalCenterPageProps> = ({ demoRole }) => {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');
  const [selectedReq, setSelectedReq] = useState<ApprovalRequest | null>(null);
  const [decisionReason, setDecisionReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadApprovals();
  }, [statusFilter]);

  const loadApprovals = async () => {
    try {
      setLoading(true);
      const res = await api.getApprovals(statusFilter === 'ALL' ? undefined : statusFilter);
      setApprovals(res.approvals);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!selectedReq) return;
    if (!decisionReason.trim()) {
      alert('Please enter a decision rationale.');
      return;
    }

    try {
      setSubmitting(true);
      if (decision === 'APPROVED') {
        await api.approveRequest(selectedReq.id, decisionReason, demoRole);
      } else {
        await api.rejectRequest(selectedReq.id, decisionReason, demoRole);
      }
      setSelectedReq(null);
      setDecisionReason('');
      loadApprovals();
    } catch (err: any) {
      alert(`Approval error: ${err.message || err}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-amber-400" />
            Human-in-the-Loop Approval Center
          </h1>
          <p className="text-xs text-slate-400">
            Cryptographically bound payload hash validation and permission boundaries for state-changing simulated actions.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-300">
          <UserCheck className="w-3.5 h-3.5 text-teal-400" />
          <span>Active Role: <b className="text-white capitalize">{demoRole.replace('_', ' ')}</b></span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['PENDING', 'APPROVED', 'REJECTED', 'ALL'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              statusFilter === st
                ? 'bg-amber-500 text-navy-950 shadow-sm'
                : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-white'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Approvals Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Approval ID</th>
                <th className="px-5 py-3">Requesting Agent</th>
                <th className="px-5 py-3">Action Type</th>
                <th className="px-5 py-3">Risk Level</th>
                <th className="px-5 py-3">Payload SHA256 Hash</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Review Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-500">Loading approval queue...</td>
                </tr>
              ) : approvals.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-500">No approval requests found matching status.</td>
                </tr>
              ) : (
                approvals.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-5 py-3.5 font-mono text-teal-400 font-semibold">{req.id}</td>
                    <td className="px-5 py-3.5 text-white font-medium">{req.agent_name}</td>
                    <td className="px-5 py-3.5 font-mono text-amber-300">{req.action_type}</td>
                    <td className="px-5 py-3.5">
                      <Badge label={req.risk_level} variant={req.risk_level} />
                    </td>
                    <td className="px-5 py-3.5 font-mono text-[11px] text-slate-400 truncate max-w-[120px]">
                      {req.payload_hash}
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge label={req.status} variant={req.status === 'PENDING' ? 'warning' : (req.status === 'APPROVED' ? 'verified' : 'high')} />
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => setSelectedReq(req)}
                        className="text-xs px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                      >
                        {req.status === 'PENDING' ? 'Review & Decisive Action' : 'View Record'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Decision Modal */}
      {selectedReq && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedReq(null)}
          title={`Approval Request Inspector: ${selectedReq.id}`}
        >
          <div className="space-y-4 text-xs">
            {/* Action Details Card */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-white text-sm">{selectedReq.action_type}</span>
                <Badge label={selectedReq.risk_level} variant={selectedReq.risk_level} />
              </div>
              <div className="text-slate-300 leading-relaxed">
                <b className="text-slate-400">Business Rationale:</b> {selectedReq.reason}
              </div>
              <div className="pt-2 border-t border-slate-800 font-mono text-[11px] text-slate-400 space-y-1">
                <div>Payload Hash (SHA256): <span className="text-teal-400">{selectedReq.payload_hash}</span></div>
                <div>Idempotency Key: <span className="text-slate-300">{selectedReq.idempotency_key}</span></div>
              </div>
            </div>

            {/* Payload Inspection */}
            <div className="space-y-1">
              <span className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider">
                Action Parameters Payload
              </span>
              <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] text-teal-300 overflow-x-auto font-mono">
                {JSON.stringify(selectedReq.payload, null, 2)}
              </pre>
            </div>

            {/* If Pending, Show Decision Input */}
            {selectedReq.status === 'PENDING' ? (
              <div className="space-y-3 pt-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Decision Rationale (Required for Audit Trail):
                  </label>
                  <textarea
                    rows={3}
                    value={decisionReason}
                    onChange={(e) => setDecisionReason(e.target.value)}
                    placeholder="Enter explicit risk and operational rationale for approving or rejecting this simulated action..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    onClick={() => handleDecision('REJECTED')}
                    disabled={submitting}
                    className="px-4 py-2 bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-800/50 font-bold rounded-xl transition flex items-center gap-1.5"
                  >
                    <XCircle className="w-4 h-4" /> Reject Action
                  </button>
                  <button
                    onClick={() => handleDecision('APPROVED')}
                    disabled={submitting}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl transition flex items-center gap-1.5 shadow-lg shadow-emerald-500/20"
                  >
                    <CheckCircle className="w-4 h-4" /> Approve & Execute
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl space-y-1">
                <div className="font-semibold text-white">Decision Recorded:</div>
                <div className="text-slate-300">Status: <b className="text-teal-400">{selectedReq.status}</b> by {selectedReq.decision_by}</div>
                <div className="text-slate-400 italic">"{selectedReq.decision_reason}"</div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
