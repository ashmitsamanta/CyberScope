import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Case } from '../types';
import { RiskScoreBadge } from '../components/RiskScoreBadge';
import {
  FolderGit2,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
  Loader2,
  Calendar,
  AlertTriangle,
  Sparkles
} from 'lucide-react';

interface Props {
  onSelectCase: (caseId: number) => void;
}

export const CasesPage: React.FC<Props> = ({ onSelectCase }) => {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  useEffect(() => {
    loadCases();
  }, [statusFilter, severityFilter]);

  const loadCases = async () => {
    try {
      setLoading(true);
      const data = await api.getCases({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        search: searchTerm || undefined,
        limit: 100,
      });
      setCases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadCases();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-cyber-accent" />
            INVESTIGATION CASE REGISTRY
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Browse and triage synthetic incident files scored by multi-factor behavioral heuristics.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-cyber-surface border border-cyber-border flex flex-wrap items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 min-w-[280px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by case number or keyword e.g. CS-1024, KYC, SMS..."
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyber-accent font-sans"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-medium border border-slate-700"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          {/* Severity filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyber-accent"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyber-accent"
          >
            <option value="">All Statuses</option>
            <option value="NEW">New</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="ESCALATED">Escalated</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>
      </div>

      {/* Cases List */}
      {loading ? (
        <div className="p-20 flex flex-col items-center justify-center text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-cyber-accent mb-3" />
          <p className="text-xs font-mono">Filtering incident ledger records...</p>
        </div>
      ) : cases.length === 0 ? (
        <div className="p-16 text-center border border-dashed border-slate-800 rounded-xl bg-cyber-card/30 text-slate-400 text-xs font-mono">
          No cases match the specified search or filter criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {cases.map((cs) => {
            const dateStr = new Date(cs.created_at).toLocaleDateString([], {
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            });

            return (
              <div
                key={cs.id}
                onClick={() => onSelectCase(cs.id)}
                className="p-4 rounded-xl bg-cyber-surface border border-cyber-border hover:border-slate-600 transition-all hover:scale-[1.01] cursor-pointer shadow-sm flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-mono text-xs font-bold text-cyber-accent group-hover:text-cyan-300 transition-colors">
                      {cs.case_number}
                    </span>
                    <RiskScoreBadge score={cs.risk_score} size="sm" />
                  </div>

                  <h3 className="font-medium text-xs text-slate-100 group-hover:text-white line-clamp-1 mb-1 font-sans">
                    {cs.title}
                  </h3>

                  <p className="text-xs text-slate-400 line-clamp-2 font-sans mb-3 leading-relaxed">
                    {cs.description || 'No complaint narrative provided.'}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px]">
                      {cs.status}
                    </span>
                    <span className="flex items-center gap-1 text-[10px] text-slate-500">
                      <Calendar className="w-3 h-3" /> {dateStr}
                    </span>
                  </div>

                  <span className="text-cyber-accent flex items-center gap-1 text-[11px] group-hover:translate-x-0.5 transition-transform font-semibold">
                    Open <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
