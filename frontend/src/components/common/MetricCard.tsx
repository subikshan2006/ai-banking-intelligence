import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  trendPositive?: boolean;
  accentColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendPositive,
  accentColor = 'teal'
}) => {
  const getIconColor = () => {
    switch (accentColor) {
      case 'amber':
        return 'text-amber-400 bg-amber-950/50 border-amber-800/40';
      case 'rose':
        return 'text-rose-400 bg-rose-950/50 border-rose-800/40';
      case 'blue':
        return 'text-blue-400 bg-blue-950/50 border-blue-800/40';
      case 'purple':
        return 'text-purple-400 bg-purple-950/50 border-purple-800/40';
      default:
        return 'text-teal-400 bg-teal-950/50 border-teal-800/40';
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        <div className={`p-2 rounded-lg border ${getIconColor()}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-white tracking-tight">{value}</span>
        {trend && (
          <span className={`text-xs font-semibold ${trendPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
            {trend}
          </span>
        )}
      </div>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  );
};
