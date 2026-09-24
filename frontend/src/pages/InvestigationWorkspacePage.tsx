import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { CaseDetail, GraphData, MoneyFlowTrace, TimelineEvent } from '../types';
import { RiskScoreBadge } from '../components/RiskScoreBadge';
import { GraphViewer } from '../components/GraphViewer';
import { MoneyFlowViewer } from '../components/MoneyFlowViewer';
import { TimelineView } from '../components/TimelineView';
import { CyberAssistChat } from '../components/CyberAssistChat';
import {
  Sparkles,
  Share2,
  AlertTriangle,
  Layers,
  Clock,
  ArrowRight,
  ShieldAlert,
  Loader2,
  Search,
  FileCheck,
  ChevronRight,
  RefreshCw,
  FolderGit2,
  CheckCircle2
} from 'lucide-react';

interface Props {
  caseId: number;
  onSelectCase: (caseId: number) => void;
}

export const InvestigationWorkspacePage: React.FC<Props> = ({ caseId, onSelectCase }) => {
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [moneyFlow, setMoneyFlow] = useState<MoneyFlowTrace | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeRightTab, setActiveRightTab] = useState<'SUMMARY' | 'TIMELINE'>('SUMMARY');
  const [graphHops, setGraphHops] = useState(1);
  const [tracingFunds, setTracingFunds] = useState(false);
  const [expandingGraph, setExpandingGraph] = useState(false);

  useEffect(() => {
    loadCaseWorkspace();
  }, [caseId]);

  const loadCaseWorkspace = async () => {
    try {
      setLoading(true);
      // Load case detail
      const detail = await api.getCaseDetail(caseId);
      setCaseDetail(detail);

      // Load initial local graph (1 hop)
      const g = await api.getCaseGraph(caseId, 1);
      setGraphData(g);
      setGraphHops(1);

      // Load case timeline
      const t = await api.getCaseTimeline(caseId);
      setTimelineEvents(t.events || []);

      // Auto-load fund trace if transactions exist
      const txs = await api.getTransactions({ case_id: caseId, limit: 1 });
      if (txs.length > 0) {
        const trace = await api.traceMoneyFlow({
          start_transaction_id: txs[0].id,
          max_hops: 3,
        });
        setMoneyFlow(trace);
      } else {
        setMoneyFlow(null);
      }
    } catch (err) {
      console.error('Failed to load workspace:', err);
    } finally {
      setLoading(false);
    }
  };

  // Step 4 & 5 in Demo Story: "Find Connections" / Expand graph to reveal syndicate
  const handleFindConnections = async () => {
    try {
      setExpandingGraph(true);
      const nextHops = graphHops < 3 ? graphHops + 1 : 1;
      const g = await api.getCaseGraph(caseId, nextHops);
      setGraphData(g);
      setGraphHops(nextHops);
    } catch (err) {
      console.error(err);
    } finally {
      setExpandingGraph(false);
    }
  };

  // Step 7 in Demo Story: "Trace Funds"
  const handleTraceFunds = async () => {
    try {
      setTracingFunds(true);
      const txs = await api.getTransactions({ case_id: caseId, limit: 1 });
      if (txs.length > 0) {
        const trace = await api.traceMoneyFlow({
          start_transaction_id: txs[0].id,
          max_hops: 4,
        });
        setMoneyFlow(trace);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setTracingFunds(false);
    }
  };

  if (loading || !caseDetail) {
    return (
      <div className="flex flex-col items-center justify-center p-28 text-slate-400">
        <Loader2 className="w-9 h-9 animate-spin text-cyber-accent mb-3" />
        <p className="text-xs font-mono">Loading investigation dossier, topological graph, and trace telemetry...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Flagship Header Banner */}
      <div className="p-5 rounded-xl bg-cyber-surface border border-cyber-border shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-cyber-card text-cyber-accent border border-cyber-border">
                CASE {caseDetail.case_number}
              </span>
              <RiskScoreBadge score={caseDetail.risk_score} size="lg" />
              {caseDetail.campaign_name && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-500/40">
                  CAMPAIGN: {caseDetail.campaign_name}
                </span>
              )}
            </div>
            <h1 className="text-lg font-mono font-bold text-slate-100">
              {caseDetail.title}
            </h1>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Source: {caseDetail.source} • Status: <strong className="text-slate-300">{caseDetail.status}</strong>
            </p>
          </div>

          {/* Quick Demo Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={handleFindConnections}
              disabled={expandingGraph}
              className="px-3.5 py-2 rounded-lg bg-cyber-accent hover:bg-cyber-accentHover text-slate-950 font-bold text-xs font-mono flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] disabled:opacity-50"
            >
              {expandingGraph ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Share2 className="w-3.5 h-3.5" />}
              Find Connections ({graphHops}-Hop)
            </button>

            <button
              onClick={handleTraceFunds}
              disabled={tracingFunds}
              className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs font-mono flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              {tracingFunds ? <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" /> : <Layers className="w-3.5 h-3.5 text-amber-400" />}
              Trace Funds
            </button>
          </div>
        </div>
      </div>

      {/* Main Investigation Split: Fraud Graph (Left) & Investigation Summary (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Fraud Graph */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-300 px-1">
            <span className="flex items-center gap-2 font-bold uppercase">
              <Share2 className="w-4 h-4 text-cyber-accent" />
              FRAUD GRAPH NEIGHBORHOOD
            </span>
            <span className="text-[11px] text-slate-500">
              EXPANSION LEVEL: <strong className="text-cyber-accent">{graphHops} HOPS</strong>
            </span>
          </div>

          <GraphViewer
            data={graphData}
            height="460px"
            enableFilters={true}
          />

          <div className="text-[11px] text-slate-400 font-mono bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between">
            <span>Graph nodes colored by entity type (Domain: Purple, Phone: Red, UPI: Amber, Account: Green).</span>
            <button
              onClick={handleFindConnections}
              className="text-cyber-accent hover:underline flex items-center gap-1 font-semibold"
            >
              Expand Ring <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Right Column: Investigation Summary / Timeline */}
        <div className="lg:col-span-5 flex flex-col rounded-xl bg-cyber-surface border border-cyber-border overflow-hidden shadow-sm">
          {/* Tab Selector */}
          <div className="flex items-center border-b border-cyber-border bg-slate-950 px-2 pt-2 gap-2 text-xs font-mono">
            <button
              onClick={() => setActiveRightTab('SUMMARY')}
              className={`px-3 py-2 border-b-2 font-bold transition-colors ${
                activeRightTab === 'SUMMARY'
                  ? 'border-cyber-accent text-cyber-accent'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              RISK SIGNALS ({caseDetail.risk_breakdown?.signals.length || 0})
            </button>
            <button
              onClick={() => setActiveRightTab('TIMELINE')}
              className={`px-3 py-2 border-b-2 font-bold transition-colors ${
                activeRightTab === 'TIMELINE'
                  ? 'border-cyber-accent text-cyber-accent'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              INCIDENT TIMELINE ({timelineEvents.length})
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-4 flex-1 overflow-y-auto max-h-[460px]">
            {activeRightTab === 'SUMMARY' ? (
              <div className="space-y-4">
                {/* Risk Explanation Summary */}
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
                  <div className="text-[10px] font-mono uppercase text-slate-500 mb-1">
                    EXPLAINABLE ASSESSMENT
                  </div>
                  <p className="text-xs text-slate-200 font-sans leading-relaxed">
                    {caseDetail.risk_breakdown?.summary || 'No risk signals recorded.'}
                  </p>

                  {/* Defined Risk Thresholds */}
                  <div className="pt-2 border-t border-slate-800/80">
                    <span className="text-[9px] font-mono uppercase text-slate-500 block mb-1.5 font-bold">
                      SEVERITY THRESHOLDS
                    </span>
                    <div className="grid grid-cols-4 gap-1 text-[10px] font-mono text-center">
                      <div className="p-1 rounded bg-slate-950/80 border border-slate-800 text-slate-400">
                        <span className="block font-bold">LOW</span> 0–39
                      </div>
                      <div className="p-1 rounded bg-slate-950/80 border border-slate-800 text-amber-500/80">
                        <span className="block font-bold">MEDIUM</span> 40–69
                      </div>
                      <div className={`p-1 rounded border ${caseDetail.risk_score >= 70 && caseDetail.risk_score < 90 ? 'bg-orange-950/60 border-orange-500 text-orange-400 font-bold ring-1 ring-orange-500/40' : 'bg-slate-950/80 border-slate-800 text-orange-400/80'}`}>
                        <span className="block font-bold">HIGH</span> 70–89
                      </div>
                      <div className={`p-1 rounded border ${caseDetail.risk_score >= 90 ? 'bg-red-950/60 border-red-500 text-red-400 font-bold ring-1 ring-red-500/40' : 'bg-slate-950/80 border-slate-800 text-red-400/80'}`}>
                        <span className="block font-bold">CRITICAL</span> 90–100
                      </div>
                    </div>
                  </div>
                </div>

                {/* Itemized Contributing Signals */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-mono uppercase text-slate-400 font-bold">
                    <span>ITEMIZED CONTRIBUTING SIGNALS</span>
                    <span className="text-cyber-accent">EXACT ARITHMETIC</span>
                  </div>
                  {caseDetail.risk_breakdown?.signals.map((sig, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1 hover:border-slate-700 transition-colors"
                    >
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="font-bold text-amber-400">{sig.code}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-500/40 font-bold">
                          +{sig.points} PTS
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 font-sans leading-relaxed">
                        {sig.explanation}
                      </p>
                    </div>
                  ))}

                  {/* Verified Arithmetic Total Footer */}
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-emerald-500/30 flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-300 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      TOTAL SIGNAL POINTS:
                    </span>
                    <span className="font-bold text-emerald-400">
                      {caseDetail.risk_breakdown?.signals.reduce((acc, s) => acc + s.points, 0).toFixed(0)} / 100 PTS ({caseDetail.risk_breakdown?.level || 'HIGH'})
                    </span>
                  </div>
                </div>

                {/* Linked Cases in Syndicate */}
                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-slate-400 font-bold block">
                    CORRELATED INCIDENT FILES
                  </span>
                  <div className="space-y-1.5 text-xs font-mono">
                    <div
                      onClick={() => onSelectCase(2)}
                      className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 flex items-center justify-between cursor-pointer transition-colors"
                    >
                      <span className="text-cyber-accent font-bold">CS-1025</span>
                      <span className="text-[10px] text-slate-400">Victim Meera Sen • 91/100 CRITICAL</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    </div>
                    <div
                      onClick={() => onSelectCase(3)}
                      className="p-2 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 flex items-center justify-between cursor-pointer transition-colors"
                    >
                      <span className="text-cyber-accent font-bold">CS-1026</span>
                      <span className="text-[10px] text-slate-400">Victim Anand Verma • 76/100 HIGH</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <TimelineView events={timelineEvents} />
            )}
          </div>
        </div>
      </div>

      {/* Bottom Split: Money Flow (Left) & CYBER-ASSIST AI (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Money Flow Visual Reconstruction (6 cols) */}
        <div className="lg:col-span-6 rounded-xl bg-cyber-surface border border-cyber-border p-5 space-y-3 shadow-sm">
          <div className="flex items-center justify-between text-xs font-mono text-slate-300">
            <span className="flex items-center gap-2 font-bold uppercase">
              <Layers className="w-4 h-4 text-amber-400" />
              SIMULATED MONEY-FLOW TRACE
            </span>
            <button
              onClick={handleTraceFunds}
              className="text-[11px] text-cyber-accent hover:underline flex items-center gap-1 font-semibold"
            >
              <RefreshCw className="w-3 h-3" /> Re-Trace
            </button>
          </div>

          <MoneyFlowViewer data={moneyFlow} loading={tracingFunds} />
        </div>

        {/* CYBER-ASSIST AI Investigator Console (6 cols) */}
        <div className="lg:col-span-6 h-[500px]">
          <CyberAssistChat caseId={caseId} />
        </div>
      </div>
    </div>
  );
};
