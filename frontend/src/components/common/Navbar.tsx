import React from 'react';
import {
  Landmark,
  ShieldAlert,
  Bell,
  Play,
  Square,
  Sparkles,
  LogOut,
  UserCheck
} from 'lucide-react';
import { Notification } from '../../types';
import { AuthUser } from '../../services/api';

interface NavbarProps {
  user: AuthUser | null;
  onLogout: () => void;
  isSimulatorRunning: boolean;
  onToggleSimulator: () => void;
  onGenerateDemoTx: () => void;
  notifications: Notification[];
  onOpenNotifications: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onLogout,
  isSimulatorRunning,
  onToggleSimulator,
  onGenerateDemoTx,
  notifications,
  onOpenNotifications
}) => {
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <header className="h-16 bg-navy-950/90 border-b border-slate-800/80 px-6 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md">
      {/* Brand & Platform Name */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-teal-500/20">
          <Landmark className="w-5 h-5 text-navy-950 font-bold" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-white tracking-wide text-base">NEXUS BANKING</span>
            <span className="text-[10px] font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/30 px-1.5 py-0.5 rounded tracking-wider">
              AI OPERATIONS
            </span>
          </div>
          <p className="text-[11px] text-slate-400">Autonomous Multi-Agent Intelligence Platform</p>
        </div>
      </div>

      {/* Controls & Quick Actions */}
      <div className="flex items-center gap-4">
        {/* Simulator Pulse & Control */}
        <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg text-xs">
          <span className="relative flex h-2.5 w-2.5">
            {isSimulatorRunning && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isSimulatorRunning ? 'bg-emerald-500' : 'bg-slate-500'}`}></span>
          </span>
          <span className="text-slate-300 font-medium">
            {isSimulatorRunning ? 'Live Stream Active' : 'Simulator Idle'}
          </span>
          <button
            onClick={onToggleSimulator}
            className={`ml-2 px-2 py-0.5 rounded text-[11px] font-medium transition flex items-center gap-1 ${
              isSimulatorRunning
                ? 'bg-rose-950 text-rose-300 border border-rose-800/50 hover:bg-rose-900'
                : 'bg-emerald-950 text-emerald-300 border border-emerald-800/50 hover:bg-emerald-900'
            }`}
          >
            {isSimulatorRunning ? <Square className="w-3 h-3" /> : <Play className="w-3 h-3" />}
            {isSimulatorRunning ? 'Stop' : 'Start'}
          </button>
        </div>

        {/* Generate Demo Transaction Button */}
        <button
          onClick={onGenerateDemoTx}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-600/20 text-teal-300 border border-teal-500/30 text-xs font-medium hover:bg-teal-600/30 transition shadow-sm"
          title="Manually emit an event into the real-time simulation"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Inject Demo Tx</span>
        </button>

        {/* Signed-in User & Role */}
        {user && (
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
            <div className="w-6 h-6 rounded-full bg-teal-500/20 border border-teal-500/40 flex items-center justify-center">
              <UserCheck className="w-3.5 h-3.5 text-teal-400" />
            </div>
            <div className="leading-tight">
              <div className="text-xs text-white font-semibold capitalize">{user.role.replace('_', ' ')}</div>
              <div className="text-[10px] text-slate-500">{user.username}</div>
            </div>
            <button
              onClick={onLogout}
              className="ml-1 p-1.5 rounded-md text-slate-400 hover:text-rose-300 hover:bg-rose-950/40 transition"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Notifications Bell */}
        <button
          onClick={onOpenNotifications}
          className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition"
        >
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-rose-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
              {unreadCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
};
