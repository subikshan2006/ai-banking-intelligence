import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Sparkles,
  RefreshCw,
  Search,
  CheckCircle,
  Eye,
  Lock,
  Cpu,
  Sliders
} from 'lucide-react';
import { api } from '../services/api';
import { FraudAlert } from '../types';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

interface FraudCenterPageProps {
  onAskAssistant: (prompt: string) => void;
  onRequestFreeze: (accountId: string, customerId: string) => void;
}

export const FraudCenterPage: React.FC<FraudCenterPageProps> = ({ onAskAssistant, onRequestFreeze }) => {
  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterRisk, setFilterRisk] = useState<string>('ALL');
  const [selectedAlert, setSelectedAlert] = useState<any | null>(null);
  const [analyzingTxId, setAnalyzingTxId] = useState<string | null>(null);

  useEffect(() => {
    loadAlerts();
  }, [filterRisk]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const res = await api.getFraudAlerts(filterRisk === 'ALL' ? undefined : filterRisk);
      setAlerts(res.alerts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInspect = async (alert: FraudAlert) => {
    try {
      const details = await api.explainTransactionRisk(alert.transaction_id);
      setSelectedAlert({ ...alert, explanation: details });
    } catch (err) {
      console.error(err);
      setSelectedAlert(alert);
    }
  };

  const handleReanalyze = async (txId: string) => {
    try {
      setAnalyzingTxId(txId);
      const res = await api.analyzeTransaction({ transaction_id: txId });
      loadAlerts();
      if (selectedAlert) {
        setSelectedAlert((prev: any) => ({ ...prev, reanalysis: res }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzingTxId(null);
    }
  };

  const handleInjectDemoAnomaly = async () => {
    try {
      await api.generateTransaction(true);
      setTimeout(loadAlerts, 1000);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            Fraud Intelligence & Anomaly Center
          </h1>
          <p className="text-xs text-slate-400">
            Rule-based detection combined with scikit-learn Isolation Forest heuristics and explainable telemetry.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleInjectDemoAnomaly}
            className="px-3.5 py-2 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 font-semibold text-xs rounded-xl transition flex items-center gap-1.5 shadow-sm"
          >
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            Inject Anomaly Scenario
          </button>
          <button
            onClick={loadAlerts}
            className="p-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white rounded-xl transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
          <button
            key={lvl}
            onClick={() => setFilterRisk(lvl)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterRisk === lvl
                ? 'bg-teal-500 text-navy-950 shadow-sm'
                : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-white'
            }`}
          >
            {lvl === 'ALL' ? 'All Alerts' : `${lvl} Risk`}
          </button>
        ))}
      </div>

      {/* Alerts Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">Alert Ref</th>
                <th className="px-5 py-3">Transaction & Customer</th>
                <th className="px-5 py-3">Risk Score</th>
                <th className="px-5 py-3">Triggered Rules</th>
                <th className="px-5 py-3">ML Anomaly</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-500">Loading alerts...</td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-500">No fraud alerts matching filter.</td>
                </tr>
              ) : (
                alerts.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-5 py-3.5 font-mono text-teal-400 font-semibold">
                      {a.id}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-white">{a.transaction_id}</div>
                      <div className="text-[11px] text-slate-400">{a.customer_id}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <span className={`font-bold text-sm ${a.risk_score >= 75 ? 'text-rose-400' : (a.risk_score >= 45 ? 'text-amber-400' : 'text-emerald-400')}`}>
                          {a.risk_score}/100
                        </span>
                        <Badge label={a.risk_level} variant={a.risk_level} />
                      </div>
                    </td>
                    <td className="px-5 py-3.5 max-w-xs truncate text-slate-300">
                      {a.triggered_rules && a.triggered_rules.length > 0 ? (
                        <span>{a.triggered_rules[0]} {a.triggered_rules.length > 1 && `(+${a.triggered_rules.length - 1})`}</span>
                      ) : (
                        <span className="text-slate-500">None</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      {a.is_ml_anomaly ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400 bg-rose-950/60 border border-rose-800/40 px-2 py-0.5 rounded">
                          <Cpu className="w-3 h-3" /> Anomaly
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400 font-mono">Normal</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge label={a.status} variant={a.status === 'OPEN' ? 'warning' : 'default'} />
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => handleInspect(a)}
                        className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Alert Modal */}
      {selectedAlert && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedAlert(null)}
          title={`Fraud Alert Inspector: ${selectedAlert.id}`}
        >
          <div className="space-y-5 text-xs">
            {/* Top Summary */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-slate-400 block">Target Transaction</span>
                <span className="text-base font-bold text-white">{selectedAlert.transaction_id}</span>
                <span className="text-[11px] text-slate-500 block">Customer: {selectedAlert.customer_id}</span>
              </div>
              <div className="text-right">
                <span className="text-slate-400 block">Synthesized Risk Score</span>
                <span className={`text-2xl font-black ${selectedAlert.risk_score >= 75 ? 'text-rose-400' : 'text-amber-400'}`}>
                  {selectedAlert.risk_score}/100
                </span>
                <Badge label={selectedAlert.risk_level} variant={selectedAlert.risk_level} />
              </div>
            </div>

            {/* Rule Engine Breakdown */}
            <div className="space-y-2">
              <h4 className="font-semibold text-white uppercase text-[11px] tracking-wider text-slate-400">
                Transparent Rule Engine Findings
              </h4>
              {selectedAlert.explanation?.rule_analysis?.length > 0 ? (
                <div className="space-y-2">
                  {selectedAlert.explanation.rule_analysis.map((r: any, idx: number) => (
                    <div key={idx} className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-rose-300">[{r.severity}] {r.rule}</span>
                      </div>
                      <p className="text-slate-400 text-[11px]">{r.reason}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 italic">No specific rule violations recorded.</p>
              )}
            </div>

            {/* Isolation Forest Output */}
            <div className="space-y-2">
              <h4 className="font-semibold text-white uppercase text-[11px] tracking-wider text-slate-400 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-teal-400" />
                Experimental Machine Learning Output
              </h4>
              <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-lg space-y-2 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-400">Model:</span>
                  <span className="text-white">scikit-learn IsolationForest (v1.0)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Raw Decision Score:</span>
                  <span className="text-teal-400">{selectedAlert.anomaly_score}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Contamination Threshold:</span>
                  <span className="text-slate-300">0.05 (Top 5% outliers)</span>
                </div>
                <p className="text-[10px] text-amber-300/80 font-sans pt-1 border-t border-slate-800">
                  Notice: Model anomaly scores represent unsupervised statistical outlier distance, not calibrated probability of fraud.
                </p>
              </div>
            </div>

            {/* Recommended Action & Escalation */}
            <div className="p-3 bg-teal-950/30 border border-teal-800/40 rounded-xl space-y-2">
              <div className="font-semibold text-teal-300">Recommended Action:</div>
              <p className="text-slate-300">{selectedAlert.recommended_action}</p>
            </div>

            {/* Actions Toolbar */}
            <div className="pt-2 flex flex-wrap gap-2 justify-end">
              <button
                onClick={() => handleReanalyze(selectedAlert.transaction_id)}
                disabled={analyzingTxId === selectedAlert.transaction_id}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-medium transition flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${analyzingTxId === selectedAlert.transaction_id ? 'animate-spin' : ''}`} />
                Re-evaluate
              </button>
              <button
                onClick={() => {
                  setSelectedAlert(null);
                  onAskAssistant(`Explain why transaction ${selectedAlert.transaction_id} was flagged.`);
                }}
                className="px-3 py-2 bg-teal-600/30 hover:bg-teal-600/40 text-teal-300 border border-teal-500/30 rounded-lg font-medium transition flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Ask AI Assistant
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
