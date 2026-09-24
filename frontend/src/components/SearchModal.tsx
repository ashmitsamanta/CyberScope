import React, { useState } from 'react';
import { api } from '../services/api';
import { Search, X, Loader2, ArrowRight, ShieldAlert, Globe, Phone, FileText } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectCase?: (caseId: number) => void;
}

export const SearchModal: React.FC<Props> = ({ isOpen, onClose, onSelectCase }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  if (!isOpen) return null;

  const handleSearch = async (queryText?: string) => {
    const q = queryText || searchTerm;
    if (!q.trim() || loading) return;

    setLoading(true);
    try {
      const res = await api.searchNaturalLanguage(q);
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    'Show accounts connected to domain secure-kyc-update.com',
    'Find cases sharing the same phone number',
    'Show transactions above ₹45,000',
    'CS-1024',
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-cyber-surface border border-cyber-border rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Search Input Bar */}
        <div className="p-4 border-b border-cyber-border flex items-center gap-3 bg-slate-950">
          <Search className="w-5 h-5 text-cyber-accent flex-shrink-0" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Type query e.g. 'Show accounts connected to domain secure-kyc-update.com'..."
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none font-mono"
            autoFocus
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="text-slate-500 hover:text-slate-300"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => handleSearch()}
            disabled={loading || !searchTerm.trim()}
            className="px-3 py-1.5 rounded-lg bg-cyber-accent hover:bg-cyber-accentHover text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Search'}
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Preset Suggestions */}
        <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-mono text-slate-400">Try:</span>
          {sampleQueries.map((sq, i) => (
            <button
              key={i}
              onClick={() => {
                setSearchTerm(sq);
                handleSearch(sq);
              }}
              className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Results Area */}
        <div className="p-4 flex-1 overflow-y-auto space-y-3">
          {loading && (
            <div className="flex items-center justify-center p-8 text-xs font-mono text-slate-400 gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-cyber-accent" />
              Parsing controlled query parameters...
            </div>
          )}

          {result && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-slate-400 pb-2 border-b border-slate-800">
                <span>INTENT: <strong className="text-cyber-accent">{result.intent}</strong></span>
                <span>MATCHES: <strong className="text-slate-200">{result.count || (result.results?.length ?? 0)}</strong></span>
              </div>

              {result.explanation && (
                <p className="text-xs text-slate-300 font-sans italic bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  {result.explanation}
                </p>
              )}

              {/* Items List */}
              <div className="space-y-2">
                {result.results && result.results.map((item: any, i: number) => (
                  <div
                    key={i}
                    onClick={() => {
                      if (item.case_number && onSelectCase) {
                        onSelectCase(item.id);
                        onClose();
                      }
                    }}
                    className="p-3 rounded-lg bg-slate-900/90 hover:bg-slate-800/80 border border-slate-800 hover:border-cyber-accent/50 cursor-pointer transition-all flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded bg-slate-800 flex items-center justify-center text-cyber-accent">
                        {item.entity_type === 'PHONE' ? <Phone className="w-3.5 h-3.5" /> : (item.entity_type === 'DOMAIN' ? <Globe className="w-3.5 h-3.5" /> : <FileText className="w-3.5 h-3.5" />)}
                      </div>
                      <div>
                        <div className="font-mono text-xs text-slate-200 font-bold">
                          {item.value || item.case_number || item.transaction_ref}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {item.entity_type || item.title || `Amount: ₹${item.amount?.toLocaleString()}`}
                        </div>
                      </div>
                    </div>
                    {item.risk_score !== undefined && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-400 border border-slate-700">
                        RISK: {item.risk_score}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
