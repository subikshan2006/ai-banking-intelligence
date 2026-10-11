import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const SimulationBanner: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-amber-950/80 via-amber-900/60 to-amber-950/80 border-b border-amber-600/30 px-4 py-1.5 text-xs text-amber-200 flex items-center justify-center gap-2">
      <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
      <span className="font-semibold tracking-wide">
        SIMULATION MODE — All customers, accounts, transactions, alerts, and loan assessments are fictional.
      </span>
      <span className="text-amber-400/80 hidden md:inline">No real financial transactions or external APIs are executed.</span>
    </div>
  );
};
