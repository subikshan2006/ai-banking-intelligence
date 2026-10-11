import React from 'react';

interface BadgeProps {
  label: string;
  variant?: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ label, variant, className = '' }) => {
  const v = (variant || label || 'default').toLowerCase();

  const getStyles = () => {
    switch (v) {
      case 'low':
      case 'verified':
      case 'success':
      case 'approved':
      case 'eligible':
      case 'passed':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-700/40';
      case 'medium':
      case 'pending':
      case 'warning':
      case 'under_review':
      case 'pending_review':
      case 'requires_manual_review':
        return 'bg-amber-950/80 text-amber-300 border-amber-700/40';
      case 'high':
      case 'critical':
      case 'rejected':
      case 'error':
      case 'failed':
      case 'ineligible':
      case 'high_risk_dti':
        return 'bg-rose-950/80 text-rose-300 border-rose-700/40';
      case 'open':
        return 'bg-amber-950/80 text-amber-300 border-amber-700/40';
      case 'info':
        return 'bg-cyan-950/80 text-cyan-300 border-cyan-700/40';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getStyles()} ${className}`}>
      {label}
    </span>
  );
};
