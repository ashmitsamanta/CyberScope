import React from 'react';
import { MoneyFlowTrace } from '../types';
import { ArrowRight, AlertTriangle, Repeat, Layers, ShieldCheck, DollarSign } from 'lucide-react';

interface Props {
  data: MoneyFlowTrace | null;
  loading?: boolean;
}

export const MoneyFlowViewer: React.FC<Props> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 border border-cyber-border rounded-xl bg-cyber-card/50 text-slate-400">
        <div className="w-8 h-8 border-2 border-cyber-accent border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-xs font-mono">Tracing graph fund movements across multi-hop accounts...</p>
      </div>
    );
  }

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl bg-cyber-card/30 text-slate-500 text-xs font-mono">
        No active money-flow trace initiated. Select an incident account or transaction to trace reachable funds.
      </div>
    );
  }

  // Group nodes by hop level
  const hopsMap = new Map<number, typeof data.nodes>();
  data.nodes.forEach((node) => {
    const list = hopsMap.get(node.hop_level) || [];
    list.push(node);
    hopsMap.set(node.hop_level, list);
  });

  const sortedHops = Array.from(hopsMap.keys()).sort((a, b) => a - b);

  return (
    <div className="space-y-4">
      {/* Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-900/80 border border-cyber-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <DollarSign className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-mono">TOTAL TRACED VOLUME</div>
            <div className="text-sm font-bold font-mono text-emerald-400">
              ₹{data.total_volume_traced.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-cyber-accent/10 border border-cyber-accent/30 flex items-center justify-center text-cyber-accent">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-mono">LAYERING DEPTH</div>
            <div className="text-sm font-bold font-mono text-slate-200">
              {data.max_hops_reached} Sequential Hops
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-mono">ANOMALY PATTERNS</div>
            <div className="text-sm font-bold font-mono text-amber-400">
              {data.detected_patterns.length} Flagged Behaviors
            </div>
          </div>
        </div>
      </div>

      {/* Pattern Warning Badges */}
      {data.detected_patterns.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.detected_patterns.map((pat, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
              <span>
                <strong className="font-mono text-rose-200">{pat.pattern}:</strong> {pat.explanation}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Multi-Hop Flow Visualization Diagram */}
      <div className="p-4 rounded-xl bg-cyber-surface border border-cyber-border overflow-x-auto">
        <div className="flex items-start gap-4 min-w-[700px] justify-between">
          {sortedHops.map((hopLevel, hopIndex) => {
            const nodesInHop = hopsMap.get(hopLevel) || [];
            const hopTitle =
              hopLevel === 0
                ? 'ORIGIN / VICTIM'
                : hopLevel === 1
                ? 'PRIMARY MULE HUB'
                : hopLevel === data.max_hops_reached
                ? 'EXIT / CASH-OUT'
                : `LAYERING HOP ${hopLevel}`;

            return (
              <React.Fragment key={hopLevel}>
                <div className="flex-1 flex flex-col items-center">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold mb-3 px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700">
                    {hopTitle}
                  </div>

                  <div className="w-full space-y-2.5">
                    {nodesInHop.map((node) => {
                      const isSource = node.role === 'SOURCE';
                      const isMule = node.role === 'MULE';
                      const borderCol = isSource
                        ? 'border-sky-500/50 bg-sky-950/20'
                        : isMule
                        ? 'border-rose-500/60 bg-rose-950/30'
                        : 'border-amber-500/40 bg-amber-950/20';

                      return (
                        <div
                          key={node.id}
                          className={`p-3 rounded-lg border ${borderCol} transition-all hover:scale-[1.02] shadow-sm`}
                        >
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="font-mono font-bold text-slate-100 truncate max-w-[130px]" title={node.label}>
                              {node.label}
                            </span>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                              {node.risk_score} RISK
                            </span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono uppercase">
                            ROLE: <span className={isMule ? 'text-rose-400 font-bold' : 'text-slate-300'}>{node.role}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {hopIndex < sortedHops.length - 1 && (
                  <div className="flex flex-col items-center justify-center self-center pt-6 text-slate-600">
                    <ArrowRight className="w-5 h-5 text-cyber-accent animate-pulse" />
                    <span className="text-[9px] font-mono text-slate-400 mt-1">FORWARD</span>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Traced Transfers Table preview */}
      <div className="rounded-xl border border-cyber-border overflow-hidden">
        <div className="bg-slate-900 px-4 py-2 text-xs font-mono font-semibold text-slate-300 border-b border-cyber-border flex justify-between">
          <span>TRACED MOVEMENTS ({data.edges.length} TRANSFERS)</span>
          <span className="text-slate-400">SORTED BY CHRONOLOGY</span>
        </div>
        <div className="max-h-48 overflow-y-auto divide-y divide-slate-800 text-xs font-mono">
          {data.edges.map((e) => (
            <div key={e.id} className="px-4 py-2 flex items-center justify-between hover:bg-slate-900/60">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">{e.source}</span>
                <ArrowRight className="w-3.5 h-3.5 text-cyber-accent" />
                <span className="text-slate-200 font-semibold">{e.target}</span>
                <span className="text-[10px] text-slate-500">[{e.channel}]</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-amber-400 font-bold">₹{e.amount.toLocaleString()}</span>
                {e.flagged && (
                  <span className="text-[9px] bg-rose-950 text-rose-400 border border-rose-500/50 px-1.5 py-0.5 rounded">
                    FLAGGED
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
