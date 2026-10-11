import React, { useEffect, useState } from 'react';
import {
  Gauge,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Sparkles,
  BarChart2,
  RefreshCw,
  Cpu
} from 'lucide-react';
import { api } from '../services/api';
import { EvaluationResponse, EvaluationCase } from '../types';
import { Badge } from '../components/common/Badge';

export const EvaluationPage: React.FC = () => {
  const [currentRun, setCurrentRun] = useState<EvaluationResponse | null>(null);
  const [pastRuns, setPastRuns] = useState<any[]>([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    loadPastRuns();
  }, []);

  const loadPastRuns = async () => {
    try {
      const runs = await api.getEvaluationRuns();
      setPastRuns(runs);
      if (runs.length > 0 && !currentRun) {
        setCurrentRun({
          evaluation_id: runs[0].id,
          timestamp: runs[0].timestamp,
          total_cases: runs[0].total_cases,
          passed_cases: runs[0].passed_cases,
          accuracy_rate: runs[0].accuracy_rate,
          mode: runs[0].mode,
          results: runs[0].case_results
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      setRunning(true);
      const res = await api.runEvaluation();
      setCurrentRun(res);
      loadPastRuns();
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Gauge className="w-5 h-5 text-teal-400" />
            Evaluation & Observability Dashboard
          </h1>
          <p className="text-xs text-slate-400">
            Automated multi-agent benchmark suite measuring intent classification accuracy, agent delegation, and response groundedness.
          </p>
        </div>
        <button
          onClick={handleRunEvaluation}
          disabled={running}
          className="px-5 py-2.5 bg-teal-500 hover:bg-teal-400 text-navy-950 font-bold text-xs rounded-xl transition flex items-center gap-2 shadow-lg shadow-teal-500/20"
        >
          <Play className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
          {running ? 'Running Benchmark Suite...' : 'Run Benchmark Suite'}
        </button>
      </div>

      {/* Benchmark Summary Card */}
      {currentRun && (
        <div className="bg-gradient-to-r from-slate-900 via-navy-900 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs font-mono text-teal-400">Run Reference: {currentRun.evaluation_id}</span>
              <h2 className="text-lg font-bold text-white mt-1">Benchmark Suite Results</h2>
              <span className="text-xs text-slate-400">Mode: {currentRun.mode}</span>
            </div>
            <div className="flex items-center gap-6 text-center">
              <div>
                <span className="text-xs text-slate-400 block">Total Cases</span>
                <span className="text-xl font-bold text-white">{currentRun.total_cases}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Passed</span>
                <span className="text-xl font-bold text-emerald-400">{currentRun.passed_cases}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Accuracy Rate</span>
                <span className="text-2xl font-black text-teal-400">{currentRun.accuracy_rate}%</span>
              </div>
            </div>
          </div>

          {/* Individual Test Cases Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Case ID</th>
                  <th className="px-4 py-2.5">Prompt</th>
                  <th className="px-4 py-2.5">Expected Intent</th>
                  <th className="px-4 py-2.5">Actual Intent</th>
                  <th className="px-4 py-2.5">Agents Dispatched</th>
                  <th className="px-4 py-2.5">Latency</th>
                  <th className="px-4 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {currentRun.results.map((tc: EvaluationCase) => (
                  <tr key={tc.case_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3 font-mono text-teal-400 font-bold">{tc.case_id}</td>
                    <td className="px-4 py-3 text-slate-200 max-w-xs truncate">{tc.prompt}</td>
                    <td className="px-4 py-3 font-mono text-slate-400">{tc.expected_intent}</td>
                    <td className="px-4 py-3 font-mono text-amber-300">{tc.actual_intent}</td>
                    <td className="px-4 py-3 text-slate-300 font-medium">
                      {tc.actual_agents.join(', ') || 'SupervisorAgent'}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-400">{tc.execution_time_ms}ms</td>
                    <td className="px-4 py-3">
                      <Badge label={tc.status} variant={tc.status === 'PASSED' ? 'verified' : 'high'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Historical Benchmark Runs */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-purple-400" />
          Evaluation Run History
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold text-[10px] uppercase">
              <tr>
                <th className="px-4 py-2">Run ID</th>
                <th className="px-4 py-2">Timestamp</th>
                <th className="px-4 py-2">Cases</th>
                <th className="px-4 py-2">Passed</th>
                <th className="px-4 py-2">Accuracy</th>
                <th className="px-4 py-2">Mode</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {pastRuns.map((r: any) => (
                <tr key={r.id} className="hover:bg-slate-800/30">
                  <td className="px-4 py-2 text-teal-400 font-bold">{r.id}</td>
                  <td className="px-4 py-2 text-slate-400">{new Date(r.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-2 text-white">{r.total_cases}</td>
                  <td className="px-4 py-2 text-emerald-400">{r.passed_cases}</td>
                  <td className="px-4 py-2 font-bold text-teal-300">{r.accuracy_rate}%</td>
                  <td className="px-4 py-2 text-slate-400">{r.mode}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
