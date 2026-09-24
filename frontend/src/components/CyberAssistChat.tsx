import React, { useState } from 'react';
import { InvestigationResponse } from '../types';
import { api } from '../services/api';
import {
  Sparkles,
  Send,
  HelpCircle,
  FileCheck,
  AlertTriangle,
  Lightbulb,
  ExternalLink,
  ShieldAlert,
  Loader2,
  ChevronRight
} from 'lucide-react';

interface Props {
  caseId?: number;
  initialQuery?: string;
}

export const CyberAssistChat: React.FC<Props> = ({ caseId }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<InvestigationResponse[]>([]);

  const promptSuggestions = [
    'Why was this case flagged?',
    'What entities connect these cases?',
    'Show the likely money flow.',
    'Which indicators are shared?',
    'What should an investigator examine next?',
    'Summarize this case.'
  ];

  const handleSend = async (qText?: string) => {
    const textToSend = qText || query;
    if (!textToSend.trim() || loading) return;

    setLoading(true);
    setQuery('');

    try {
      const response = await api.queryCyberAssist({
        query: textToSend,
        case_id: caseId || undefined,
      });
      setHistory((prev) => [response, ...prev]);
    } catch (err: any) {
      console.error('Cyber-Assist inquiry error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#080D18] rounded-xl border border-cyber-border overflow-hidden shadow-lg">
      {/* Console Header */}
      <div className="p-3 bg-slate-950 border-b border-cyber-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-cyber-accent/20 border border-cyber-accent/40 flex items-center justify-center text-cyber-accent">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-mono text-xs font-bold text-slate-100 flex items-center gap-1.5">
              CYBER-ASSIST <span className="text-[10px] text-cyber-accent font-medium">AI INVESTIGATOR</span>
            </span>
            <span className="block text-[9px] text-slate-400 font-sans">
              Strictly evidence-grounded reasoning • Zero hallucinations
            </span>
          </div>
        </div>

        <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-500/40 text-emerald-400">
          GROUNDED MODE
        </span>
      </div>

      {/* Suggested Inquiries */}
      <div className="p-2.5 bg-slate-900/60 border-b border-slate-800/80 flex flex-wrap gap-1.5">
        {promptSuggestions.map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSend(prompt)}
            disabled={loading}
            className="text-[11px] font-mono px-2.5 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700 hover:border-cyber-accent/50 transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <ChevronRight className="w-3 h-3 text-cyber-accent" />
            {prompt}
          </button>
        ))}
      </div>

      {/* Interactive Response Stream */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {history.length === 0 && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
            <HelpCircle className="w-10 h-10 text-slate-600 mb-3" />
            <h4 className="text-xs font-mono font-bold text-slate-300 uppercase mb-1">
              Investigator Intelligence Terminal
            </h4>
            <p className="text-xs max-w-sm text-slate-400 mb-4">
              Select one of the suggested prompts above or submit a question regarding indicators, money flow, or syndicates.
            </p>
          </div>
        )}

        {loading && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-900/70 border border-cyber-border text-xs font-mono text-slate-300 animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin text-cyber-accent" />
            Grounding structured evidence, tracing relationships, and constructing defense report...
          </div>
        )}

        {history.map((item, idx) => (
          <div key={idx} className="space-y-3.5 bg-slate-900/90 rounded-xl p-4 border border-cyber-border shadow-md">
            {/* User Inquiry Tag */}
            <div className="flex items-center gap-2 text-xs font-mono text-cyber-accent font-semibold pb-2 border-b border-slate-800">
              <span className="w-1.5 h-1.5 rounded-full bg-cyber-accent" />
              INVESTIGATOR: "{item.query}"
            </div>

            {/* Answer Body */}
            <div className="text-xs text-slate-200 leading-relaxed font-sans prose prose-invert max-w-none whitespace-pre-wrap">
              {item.answer}
            </div>

            {/* Structured Evidence Section */}
            {item.observed_evidence && item.observed_evidence.length > 0 && (
              <div className="p-3 rounded-lg bg-[#0A0E18] border border-slate-800 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold flex items-center gap-1.5">
                  <FileCheck className="w-3.5 h-3.5" /> Observed Grounded Evidence
                </span>
                <ul className="text-xs text-slate-300 space-y-1">
                  {item.observed_evidence.map((obs, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{obs}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Calculated Signals Breakdown */}
            {item.calculated_signals && item.calculated_signals.length > 0 && (
              <div className="p-3 rounded-lg bg-[#0A0E18] border border-slate-800 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-amber-400 font-bold flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" /> Calculated Risk Signals
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {item.calculated_signals.map((sig, i) => (
                    <span
                      key={i}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/60 border border-amber-500/40 text-amber-300"
                    >
                      {sig.code} (+{sig.points} pts)
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Next Actions */}
            {item.recommended_next_steps && item.recommended_next_steps.length > 0 && (
              <div className="p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/30 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-cyan-400 font-bold flex items-center gap-1.5">
                  <Lightbulb className="w-3.5 h-3.5" /> Recommended Defensive Actions
                </span>
                <ol className="text-xs text-slate-300 space-y-1 list-decimal list-inside">
                  {item.recommended_next_steps.map((step, i) => (
                    <li key={i} className="leading-snug">{step}</li>
                  ))}
                </ol>
              </div>
            )}

            {/* Citations Badges */}
            {item.evidence_citations && item.evidence_citations.length > 0 && (
              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] font-mono text-slate-500 mr-1">EVIDENCE CITATIONS:</span>
                {item.evidence_citations.map((cite, i) => (
                  <span
                    key={i}
                    title={cite.summary}
                    className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 hover:border-cyber-accent transition-colors"
                  >
                    <ExternalLink className="w-2.5 h-2.5 text-cyber-accent" />
                    {cite.tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3 bg-slate-950 border-t border-cyber-border flex items-center gap-2"
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask CYBER-ASSIST about indicators, money flow, or entities..."
          disabled={loading}
          className="flex-1 bg-cyber-surface border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyber-accent font-sans"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-3.5 py-2 rounded-lg bg-cyber-accent hover:bg-cyber-accentHover text-slate-950 font-semibold text-xs flex items-center gap-1.5 disabled:opacity-40 transition-colors shadow-sm"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          Inquire
        </button>
      </form>
    </div>
  );
};
