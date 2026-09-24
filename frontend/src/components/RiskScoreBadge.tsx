import React from 'react';

interface Props {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const RiskScoreBadge: React.FC<Props> = ({ score, size = 'md', showLabel = true }) => {
  const getLevel = (s: number) => {
    if (s >= 90) return { label: 'CRITICAL', bg: 'bg-rose-950/70', border: 'border-rose-500/80', text: 'text-rose-400', glow: 'shadow-[0_0_12px_rgba(244,63,94,0.35)]' };
    if (s >= 70) return { label: 'HIGH', bg: 'bg-orange-950/70', border: 'border-orange-500/80', text: 'text-orange-400', glow: 'shadow-[0_0_10px_rgba(249,115,22,0.3)]' };
    if (s >= 40) return { label: 'MEDIUM', bg: 'bg-amber-950/70', border: 'border-amber-500/80', text: 'text-amber-400', glow: '' };
    return { label: 'LOW', bg: 'bg-emerald-950/70', border: 'border-emerald-500/80', text: 'text-emerald-400', glow: '' };
  };

  const level = getLevel(score);

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-semibold'
  }[size];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded border ${level.bg} ${level.border} ${level.text} ${level.glow} ${sizeClasses} font-mono tracking-wide`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      {score.toFixed(0)}/100
      {showLabel && <span className="font-sans font-medium text-[10px] uppercase opacity-90">({level.label})</span>}
    </span>
  );
};
