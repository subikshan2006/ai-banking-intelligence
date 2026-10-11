import React, { useEffect, useState } from 'react';
import {
  FileSpreadsheet,
  Calculator,
  Sliders,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Percent,
  Calendar,
  Layers
} from 'lucide-react';
import { api } from '../services/api';
import { LoanApplication, LoanScenario } from '../types';
import { Badge } from '../components/common/Badge';

export const LoanCenterPage: React.FC = () => {
  // Calculator State
  const [calcPrincipal, setCalcPrincipal] = useState<number>(500000);
  const [calcRate, setCalcRate] = useState<number>(10.5);
  const [calcTenure, setCalcTenure] = useState<number>(36);
  const [emiOutput, setEmiOutput] = useState<any>(null);

  // Eligibility Evaluation State
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('CUST1001');
  const [evalAmount, setEvalAmount] = useState<number>(500000);
  const [evalTenure, setEvalTenure] = useState<number>(36);
  const [evalResult, setEvalResult] = useState<any | null>(null);
  const [evaluating, setEvaluating] = useState<boolean>(false);

  // Applications List State
  const [loans, setLoans] = useState<LoanApplication[]>([]);
  const [loadingLoans, setLoadingLoans] = useState<boolean>(true);

  // What-If Scenarios
  const [comparisonResult, setComparisonResult] = useState<any | null>(null);

  useEffect(() => {
    loadApplications();
    recalculateEmi();
    runInitialComparison();
  }, []);

  useEffect(() => {
    recalculateEmi();
  }, [calcPrincipal, calcRate, calcTenure]);

  const loadApplications = async () => {
    try {
      setLoadingLoans(true);
      const res = await api.getLoans();
      setLoans(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingLoans(false);
    }
  };

  const recalculateEmi = async () => {
    try {
      const res = await api.calculateEmi({
        principal: calcPrincipal,
        tenure_months: calcTenure,
        interest_rate: calcRate
      });
      setEmiOutput(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleEvaluateEligibility = async () => {
    try {
      setEvaluating(true);
      const res = await api.evaluateLoan({
        customer_id: selectedCustomerId,
        requested_amount: evalAmount,
        tenure_months: evalTenure,
        purpose: 'Personal'
      });
      setEvalResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setEvaluating(false);
    }
  };

  const runInitialComparison = async () => {
    try {
      const res = await api.compareLoans([
        { principal: 300000, tenure_months: 24, interest_rate: 10.5 },
        { principal: 500000, tenure_months: 36, interest_rate: 10.5 },
        { principal: 800000, tenure_months: 48, interest_rate: 11.0 }
      ]);
      setComparisonResult(res);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <FileSpreadsheet className="w-5 h-5 text-teal-400" />
          Loan Assessment & What-If Credit Simulator
        </h1>
        <p className="text-xs text-slate-400">
          Deterministic mathematical amortization, transparent DTI thresholds, and policy-grounded risk scoring.
        </p>
      </div>

      {/* Top Grid: Interactive EMI Calculator & Customer Eligibility Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Interactive EMI Calculator */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Calculator className="w-4 h-4 text-teal-400" />
              Standard Amortization Calculator
            </h2>
            <span className="text-[11px] font-mono text-slate-400">Deterministic Formula</span>
          </div>

          <div className="space-y-3 text-xs">
            {/* Principal Slider */}
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Principal Amount</span>
                <span className="font-bold text-white">₹{calcPrincipal.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="50000"
                max="2500000"
                step="25000"
                value={calcPrincipal}
                onChange={(e) => setCalcPrincipal(Number(e.target.value))}
                className="w-full accent-teal-400 cursor-pointer"
              />
            </div>

            {/* Interest Rate Slider */}
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Annual Interest Rate</span>
                <span className="font-bold text-teal-400">{calcRate}% p.a.</span>
              </div>
              <input
                type="range"
                min="7.0"
                max="18.0"
                step="0.25"
                value={calcRate}
                onChange={(e) => setCalcRate(Number(e.target.value))}
                className="w-full accent-teal-400 cursor-pointer"
              />
            </div>

            {/* Tenure Slider */}
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Tenure Duration</span>
                <span className="font-bold text-white">{calcTenure} Months ({(calcTenure / 12).toFixed(1)} yrs)</span>
              </div>
              <input
                type="range"
                min="6"
                max="84"
                step="6"
                value={calcTenure}
                onChange={(e) => setCalcTenure(Number(e.target.value))}
                className="w-full accent-teal-400 cursor-pointer"
              />
            </div>
          </div>

          {/* EMI Output Card */}
          {emiOutput && (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 grid grid-cols-3 gap-2 text-center">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Monthly EMI</span>
                <span className="text-base font-bold text-teal-400">₹{emiOutput.monthly_emi.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Total Interest</span>
                <span className="text-sm font-semibold text-slate-300">₹{emiOutput.total_interest.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold block">Cumulative Payout</span>
                <span className="text-sm font-semibold text-white">₹{emiOutput.total_repayment.toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>

        {/* Customer Eligibility Simulator */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                Customer Eligibility Evaluation
              </h2>
              <span className="text-[11px] text-slate-500">Prudential DTI Policy</span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs pt-3 mb-4">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Customer</label>
                <select
                  value={selectedCustomerId}
                  onChange={(e) => setSelectedCustomerId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none"
                >
                  <option value="CUST1001">CUST1001 (Aarav)</option>
                  <option value="CUST1002">CUST1002 (Priya)</option>
                  <option value="CUST1003">CUST1003 (Rohan)</option>
                  <option value="CUST1004">CUST1004 (Ananya)</option>
                  <option value="CUST1007">CUST1007 (Kabir)</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Amount</label>
                <input
                  type="number"
                  value={evalAmount}
                  onChange={(e) => setEvalAmount(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Tenure (Mo)</label>
                <input
                  type="number"
                  value={evalTenure}
                  onChange={(e) => setEvalTenure(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none"
                />
              </div>
            </div>

            <button
              onClick={handleEvaluateEligibility}
              disabled={evaluating}
              className="w-full py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs rounded-lg transition shadow-md"
            >
              {evaluating ? 'Evaluating...' : 'Run Credit Assessment'}
            </button>
          </div>

          {/* Assessment Result Output */}
          {evalResult && (
            <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2 text-xs mt-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-slate-400 block text-[11px]">Assessment Verdict:</span>
                  <Badge label={evalResult.assessment_result} variant={evalResult.assessment_result === 'ELIGIBLE' ? 'low' : 'high'} />
                </div>
                <div className="text-right">
                  <span className="text-slate-400 block text-[11px]">Projected DTI Ratio:</span>
                  <span className={`text-base font-bold ${evalResult.debt_to_income_ratio <= 40 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {evalResult.debt_to_income_ratio}%
                  </span>
                </div>
              </div>
              <div className="space-y-1 text-[11px] text-slate-300 pt-1 border-t border-slate-800">
                {evalResult.positive_factors?.map((f: string, idx: number) => (
                  <div key={idx} className="text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle className="w-3 h-3 shrink-0" /> {f}
                  </div>
                ))}
                {evalResult.caution_factors?.map((f: string, idx: number) => (
                  <div key={idx} className="text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-3 h-3 shrink-0" /> {f}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Scenario Comparison Table */}
      {comparisonResult && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              What-If Loan Scenario Comparison
            </h3>
            <span className="text-xs text-slate-400">{comparisonResult.comparison_summary}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold text-[10px] uppercase">
                <tr>
                  <th className="px-4 py-2.5">Scenario</th>
                  <th className="px-4 py-2.5">Principal</th>
                  <th className="px-4 py-2.5">Tenure</th>
                  <th className="px-4 py-2.5">Rate</th>
                  <th className="px-4 py-2.5">Monthly EMI</th>
                  <th className="px-4 py-2.5">Total Interest</th>
                  <th className="px-4 py-2.5">Total Repayment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {comparisonResult.scenarios.map((sc: LoanScenario) => (
                  <tr key={sc.scenario_id} className="hover:bg-slate-800/30">
                    <td className="px-4 py-2.5 font-bold text-white">{sc.scenario_id}</td>
                    <td className="px-4 py-2.5 font-mono">₹{sc.principal.toLocaleString()}</td>
                    <td className="px-4 py-2.5">{sc.tenure_months} Mo</td>
                    <td className="px-4 py-2.5 text-teal-400 font-semibold">{sc.interest_rate}%</td>
                    <td className="px-4 py-2.5 font-bold text-teal-300">₹{sc.monthly_emi.toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-slate-300">₹{sc.total_interest.toLocaleString()}</td>
                    <td className="px-4 py-2.5 font-semibold text-white">₹{sc.total_repayment.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Existing Loan Applications Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white">Simulated Loan Applications Queue</h3>
          <span className="text-xs text-slate-500">{loans.length} Recorded Applications</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-5 py-3">App ID</th>
                <th className="px-5 py-3">Customer</th>
                <th className="px-5 py-3">Requested Amount</th>
                <th className="px-5 py-3">Tenure</th>
                <th className="px-5 py-3">Monthly EMI</th>
                <th className="px-5 py-3">DTI Ratio</th>
                <th className="px-5 py-3">Assessment</th>
                <th className="px-5 py-3">Approval Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loadingLoans ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-slate-500">Loading loan applications...</td>
                </tr>
              ) : (
                loans.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-5 py-3.5 font-mono text-teal-400 font-semibold">{l.id}</td>
                    <td className="px-5 py-3.5 text-white font-medium">{l.customer_id}</td>
                    <td className="px-5 py-3.5 font-bold text-white">₹{l.requested_amount.toLocaleString()}</td>
                    <td className="px-5 py-3.5 text-slate-300">{l.tenure_months} Mo</td>
                    <td className="px-5 py-3.5 text-teal-400 font-semibold">₹{l.estimated_emi.toLocaleString()}</td>
                    <td className="px-5 py-3.5 font-bold text-slate-200">{l.dti_ratio}%</td>
                    <td className="px-5 py-3.5">
                      <Badge label={l.assessment_result} variant={l.assessment_result === 'ELIGIBLE' ? 'low' : 'high'} />
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge label={l.approval_status} variant={l.approval_status === 'APPROVED' ? 'low' : (l.approval_status === 'REJECTED' ? 'high' : 'medium')} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
