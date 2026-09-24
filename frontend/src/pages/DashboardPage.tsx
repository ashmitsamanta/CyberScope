import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DashboardStats, Case, Campaign } from '../types';
import { RiskScoreBadge } from '../components/RiskScoreBadge';
import {
  FolderGit2,
  ShieldAlert,
  Flame,
  Share2,
  Target,
  CreditCard,
  ArrowUpRight,
  TrendingUp,
  Activity,
  PlusCircle,
  ExternalLink,
  Loader2
} from 'lucide-react';

interface Props {
  onSelectCase: (caseId: number) => void;
  onNavigateTab: (tab: string) => void;
}

export const DashboardPage: React.FC<Props> = ({ onSelectCase, onNavigateTab }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [ingestModalOpen, setIngestModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [ingesting, setIngesting] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;

    setIngesting(true);
    try {
      const res = await api.ingestReport({
        title: newTitle || 'Reported Cyber Fraud Incident',
        content: newContent,
      });
      setIngestModalOpen(false);
      setNewTitle('');
      setNewContent('');
      await loadDashboard();
      if (res.case_id) {
        onSelectCase(res.case_id);
      }
    } catch (err) {
      console.error('Ingestion failed:', err);
    } finally {
      setIngesting(false);
    }
  };

  if (loading || !stats) {
    return (
      <div className="flex flex-col items-center justify-center p-24 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-cyber-accent mb-3" />
        <p className="text-xs font-mono">Aggregating telemetry from fraud ledger and behavioral graph...</p>
      </div>
    );
  }

  const kpis = [
    { label: 'TOTAL INCIDENTS', value: stats.kpis.total_cases, icon: FolderGit2, color: 'text-slate-200', bg: 'bg-slate-800/40', border: 'border-slate-700' },
    { label: 'HIGH RISK CASES', value: stats.kpis.high_risk_cases, icon: ShieldAlert, color: 'text-orange-400', bg: 'bg-orange-950/20', border: 'border-orange-500/40' },
    { label: 'CRITICAL CASES', value: stats.kpis.critical_cases, icon: Flame, color: 'text-rose-400', bg: 'bg-rose-950/30', border: 'border-rose-500/50', glow: 'shadow-[0_0_15px_rgba(244,63,94,0.15)]' },
    { label: 'LINKED ENTITIES', value: stats.kpis.linked_entities, icon: Share2, color: 'text-cyber-accent', bg: 'bg-cyan-950/20', border: 'border-cyan-500/40' },
    { label: 'DETECTED CAMPAIGNS', value: stats.kpis.detected_campaigns, icon: Target, color: 'text-purple-400', bg: 'bg-purple-950/20', border: 'border-purple-500/40' },
    { label: 'TRANSACTIONS ANALYZED', value: stats.kpis.transactions_analyzed, icon: CreditCard, color: 'text-emerald-400', bg: 'bg-emerald-950/20', border: 'border-emerald-500/40' },
  ];

  return (
    <div className="space-y-6">
      {/* Title & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            INTELLIGENCE OVERVIEW
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Cross-incident correlation, anomaly telemetry, and coordinated syndicate tracking.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onSelectCase(1)}
            className="px-3.5 py-1.5 rounded-lg bg-cyber-accent hover:bg-cyber-accentHover text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(6,182,212,0.25)]"
          >
            <Activity className="w-3.5 h-3.5" />
            Launch Live Demo (Phantom KYC)
          </button>
          <button
            onClick={() => setIngestModalOpen(true)}
            className="px-3.5 py-1.5 rounded-lg bg-cyber-card hover:bg-slate-800 text-slate-200 border border-cyber-border text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5 text-cyber-accent" />
            Ingest Evidence
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3.5">
        {kpis.map((kpi, i) => {
          const Icon = kpi.icon;
          return (
            <div
              key={i}
              className={`p-4 rounded-xl border ${kpi.border} ${kpi.bg} ${kpi.glow || ''} transition-all hover:scale-[1.02] flex flex-col justify-between`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono text-slate-400 font-medium tracking-wide">
                  {kpi.label}
                </span>
                <Icon className={`w-4 h-4 ${kpi.color}`} />
              </div>
              <div className={`text-2xl font-bold font-mono ${kpi.color}`}>
                {kpi.value}
              </div>
            </div>
          );
        })}
      </div>

      {/* Middle Split: Risk Distribution & Active Campaigns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Risk Spectrum Card (5 cols) */}
        <div className="lg:col-span-5 p-5 rounded-xl bg-cyber-surface border border-cyber-border flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
                CASE RISK SPECTRUM
              </h2>
              <span className="text-[10px] font-mono text-slate-500">42 TOTAL</span>
            </div>

            <div className="space-y-3">
              {stats.risk_distribution.map((r, i) => {
                const total = stats.kpis.total_cases || 42;
                const pct = Math.round((r.count / total) * 100);
                return (
                  <div key={i} className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-300 font-medium">{r.level} SEVERITY</span>
                      <span className="text-slate-400">
                        {r.count} cases ({pct}%)
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: r.color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-5 p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400 font-sans leading-relaxed">
            <strong className="text-slate-300 font-mono">Defensive Philosophy:</strong> Risk scores quantify evidentiary clustering across multi-hop transactions rather than isolated events.
          </div>
        </div>

        {/* Active Campaigns Card (7 cols) */}
        <div className="lg:col-span-7 p-5 rounded-xl bg-cyber-surface border border-cyber-border shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                <Target className="w-4 h-4 text-purple-400" />
                COORDINATED FRAUD CAMPAIGNS
              </h2>
              <button
                onClick={() => onNavigateTab('campaigns')}
                className="text-[11px] font-mono text-cyber-accent hover:underline flex items-center gap-1"
              >
                View All <ArrowUpRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-3">
              {stats.active_campaigns.map((camp) => (
                <div
                  key={camp.id}
                  onClick={() => onNavigateTab('campaigns')}
                  className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-purple-500/60 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-bold text-slate-100 group-hover:text-purple-300 transition-colors">
                      {camp.name}
                    </span>
                    <RiskScoreBadge score={camp.risk_score} size="sm" />
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-1 mb-2 font-sans">
                    {camp.description}
                  </p>
                  <div className="flex items-center gap-3 text-[10px] font-mono text-slate-500">
                    <span>CASES: <strong className="text-slate-300">{camp.case_count}</strong></span>
                    <span>ENTITIES: <strong className="text-slate-300">{camp.entity_count}</strong></span>
                    <span>STATUS: <strong className="text-emerald-400">{camp.status}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Table: High-Risk Incident Queue */}
      <div className="p-5 rounded-xl bg-cyber-surface border border-cyber-border shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              PRIORITY INVESTIGATION QUEUE
            </h2>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Incident files exhibiting highest compound risk signals requiring analyst attention.
            </p>
          </div>
          <button
            onClick={() => onNavigateTab('cases')}
            className="text-[11px] font-mono text-cyber-accent hover:underline flex items-center gap-1"
          >
            Full Case Registry <ArrowUpRight className="w-3 h-3" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-mono uppercase text-slate-400 bg-slate-900/60">
                <th className="py-2.5 px-3">CASE ID</th>
                <th className="py-2.5 px-3">INCIDENT TITLE</th>
                <th className="py-2.5 px-3">SEVERITY</th>
                <th className="py-2.5 px-3">STATUS</th>
                <th className="py-2.5 px-3">INVESTIGATION RISK</th>
                <th className="py-2.5 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-xs font-sans">
              {stats.recent_high_risk_cases.map((cs) => (
                <tr
                  key={cs.id}
                  onClick={() => onSelectCase(cs.id)}
                  className="hover:bg-slate-900/80 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-3 font-mono font-bold text-cyber-accent">
                    {cs.case_number}
                  </td>
                  <td className="py-3 px-3 font-medium text-slate-200 group-hover:text-cyber-accent transition-colors">
                    {cs.title}
                  </td>
                  <td className="py-3 px-3">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                      cs.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-400 border border-rose-500/40' : 'bg-orange-950 text-orange-400 border border-orange-500/40'
                    }`}>
                      {cs.severity}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {cs.status}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <RiskScoreBadge score={cs.risk_score} size="sm" />
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button className="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-800 group-hover:bg-cyber-accent group-hover:text-slate-950 text-slate-300 font-semibold transition-colors">
                      Investigate →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ingest Modal */}
      {ingestModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-cyber-surface border border-cyber-border rounded-xl p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-mono font-bold text-slate-100 flex items-center gap-2">
              <PlusCircle className="w-4 h-4 text-cyber-accent" />
              INGEST SYNTHETIC EVIDENCE REPORT
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              Submit raw unformatted SMS, complaint, or fraud report. Entities will be extracted, normalized, and linked to the fraud graph automatically.
            </p>

            <form onSubmit={handleIngest} className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">INCIDENT TITLE</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Fake Bank KYC Phishing Complaint"
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-cyber-accent font-sans"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">RAW CONTENT / MESSAGE TEXT</label>
                <textarea
                  rows={4}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="Paste message with links, phones, or UPIs e.g. 'Urgent: Verify your account at https://test-fake-portal.com and transfer ₹500 to quickmule@okaxis'..."
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-cyber-accent font-mono"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIngestModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 text-xs font-mono"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={ingesting}
                  className="px-4 py-1.5 rounded-lg bg-cyber-accent hover:bg-cyber-accentHover text-slate-950 font-bold text-xs flex items-center gap-1.5"
                >
                  {ingesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Ingest & Correlate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
