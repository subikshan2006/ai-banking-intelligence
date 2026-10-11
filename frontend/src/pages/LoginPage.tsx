import React, { useState } from 'react';
import { Landmark, LogIn, ShieldAlert, UserCheck, KeyRound } from 'lucide-react';
import { api } from '../services/api';
import { AuthUser } from '../services/api';

interface LoginPageProps {
  onLogin: (user: AuthUser) => void;
}

const DEMO_CREDENTIALS = [
  { username: 'manager', password: 'Manager@123', role: 'Branch Manager', note: 'Full approval authority' },
  { username: 'risk_analyst', password: 'Risk@123', role: 'Risk Analyst', note: 'Read + monitoring only' },
  { username: 'compliance_officer', password: 'Compliance@123', role: 'Compliance Officer', note: 'Freeze / policy exceptions' }
];

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!username.trim() || !password) {
      setError('Please enter both username and password.');
      return;
    }
    try {
      setLoading(true);
      const user = await api.login(username.trim(), password);
      onLogin(user);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const quickFill = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
    setError('');
  };

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 flex items-center justify-center p-6 font-sans selection:bg-teal-500 selection:text-navy-950">
      <div className="w-full max-w-4xl grid lg:grid-cols-[1.1fr_1fr] rounded-2xl overflow-hidden border border-slate-800 shadow-2xl shadow-teal-500/5">
        {/* Left Panel */}
        <div className="bg-gradient-to-br from-navy-900 via-navy-950 to-navy-900 p-8 flex flex-col justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <Landmark className="w-6 h-6 text-navy-950 font-bold" />
            </div>
            <div>
              <div className="font-bold text-white tracking-wide text-lg">NEXUS BANKING</div>
              <div className="text-[10px] font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30 px-1.5 py-0.5 rounded tracking-wider inline-block mt-0.5">
                AI OPERATIONS
              </div>
            </div>
          </div>

          <div className="space-y-4 my-8">
            <h1 className="text-2xl font-bold text-white leading-tight">
              Sign in to the Autonomous Multi-Agent Intelligence Platform
            </h1>
            <p className="text-xs text-slate-400 leading-relaxed">
              Role-based access for the simulated banking operations console. Each role
              carries a discrete permission boundary enforced server-side by signings and audit logs.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-teal-300 bg-teal-500/10 border border-teal-500/20 rounded-lg px-3 py-2">
              <ShieldAlert className="w-4 h-4" />
              All approvals and role decisions are recorded to the immutable audit trail.
            </div>
          </div>

          <p className="text-[10px] text-slate-500">Simulation environment · No real bank data leaves this demo</p>
        </div>

        {/* Right Panel - Login Form */}
        <div className="bg-slate-950 p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <KeyRound className="w-4 h-4 text-teal-400" />
              <span>Authorized Personnel Only</span>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1 uppercase tracking-wider">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                placeholder="e.g. manager"
                className="w-full bg-navy-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1 uppercase tracking-wider">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full bg-navy-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>

            {error && (
              <div className="text-xs text-rose-400 bg-rose-950/40 border border-rose-800/50 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-bold rounded-xl py-2.5 transition shadow-lg shadow-teal-500/20"
            >
              <LogIn className="w-4 h-4" />
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6">
            <div className="flex items-center gap-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              <UserCheck className="w-3.5 h-3.5" />
              Demo Accounts
            </div>
            <div className="space-y-2">
              {DEMO_CREDENTIALS.map((c) => (
                <button
                  key={c.username}
                  type="button"
                  onClick={() => quickFill(c.username, c.password)}
                  className="w-full text-left bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg px-3 py-2 transition"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white font-semibold">{c.role}</span>
                    <span className="text-[10px] font-mono text-teal-400">{c.username}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{c.note}</div>
                </button>
              ))}
            </div>
            <p className="text-[10px] text-slate-600 mt-2">Click an account to auto-fill, then press Sign In.</p>
          </div>
        </div>
      </div>
    </div>
  );
};