import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Transaction, MoneyFlowTrace } from '../types';
import { MoneyFlowViewer } from '../components/MoneyFlowViewer';
import {
  CreditCard,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
  Loader2,
  Calendar,
  X,
  ExternalLink,
  Layers
} from 'lucide-react';

interface Props {
  onSelectCase?: (caseId: number) => void;
}

export const TransactionsPage: React.FC<Props> = ({ onSelectCase }) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [channelFilter, setChannelFilter] = useState('');
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [traceData, setTraceData] = useState<MoneyFlowTrace | null>(null);
  const [loadingTrace, setLoadingTrace] = useState(false);

  useEffect(() => {
    loadTransactions();
  }, [channelFilter]);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const data = await api.getTransactions({
        channel: channelFilter || undefined,
        limit: 100,
      });
      setTransactions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectTx = async (tx: Transaction) => {
    setSelectedTx(tx);
    try {
      setLoadingTrace(true);
      const trace = await api.traceMoneyFlow({
        start_transaction_id: tx.id,
        max_hops: 4,
      });
      setTraceData(trace);
    } catch (err) {
      console.error('Trace error:', err);
    } finally {
      setLoadingTrace(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-cyber-accent" />
            FINANCIAL TRANSACTION EXPLORER
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Audit simulated ledger movements, identify structured bursts, and trace layering hops.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={channelFilter}
            onChange={(e) => setChannelFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyber-accent"
          >
            <option value="">All Payment Channels</option>
            <option value="UPI">UPI</option>
            <option value="IMPS">IMPS</option>
            <option value="NEFT">NEFT</option>
            <option value="RTGS">RTGS</option>
          </select>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="rounded-xl bg-cyber-surface border border-cyber-border overflow-hidden shadow-sm">
        <div className="p-3 bg-slate-900/80 border-b border-cyber-border flex justify-between items-center text-xs font-mono">
          <span className="text-slate-400 font-semibold">TRANSACTIONS LOGGED ({transactions.length})</span>
          <span className="text-[10px] text-slate-500">CLICK ROW TO TRACE MONEY FLOW</span>
        </div>

        {loading ? (
          <div className="p-20 flex flex-col items-center justify-center text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-cyber-accent mb-3" />
            <p className="text-xs font-mono">Loading ledger telemetry...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] font-mono uppercase text-slate-400 bg-slate-950/60">
                  <th className="py-2.5 px-3">TIMESTAMP</th>
                  <th className="py-2.5 px-3">TX REF</th>
                  <th className="py-2.5 px-3">ORIGINATOR (SENDER)</th>
                  <th className="py-2.5 px-3">BENEFICIARY (RECEIVER)</th>
                  <th className="py-2.5 px-3">AMOUNT</th>
                  <th className="py-2.5 px-3">CHANNEL</th>
                  <th className="py-2.5 px-3">STATUS</th>
                  <th className="py-2.5 px-3 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-xs font-mono">
                {transactions.map((tx) => {
                  const dateStr = new Date(tx.timestamp).toLocaleString([], {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  });
                  const isFlagged = tx.amount >= 40000 || tx.status === 'FLAGGED';

                  return (
                    <tr
                      key={tx.id}
                      onClick={() => handleInspectTx(tx)}
                      className={`hover:bg-slate-900/80 cursor-pointer transition-colors ${
                        selectedTx?.id === tx.id ? 'bg-slate-900 border-l-2 border-cyber-accent' : ''
                      }`}
                    >
                      <td className="py-3 px-3 text-slate-400 whitespace-nowrap">{dateStr}</td>
                      <td className="py-3 px-3 font-bold text-cyber-accent">{tx.transaction_ref}</td>
                      <td className="py-3 px-3 text-slate-300 truncate max-w-[150px]">{tx.sender_value || `Entity #${tx.sender_entity_id}`}</td>
                      <td className="py-3 px-3 text-slate-200 font-semibold truncate max-w-[150px]">{tx.receiver_value || `Entity #${tx.receiver_entity_id}`}</td>
                      <td className="py-3 px-3">
                        <span className={`font-bold ${isFlagged ? 'text-amber-400' : 'text-slate-200'}`}>
                          ₹{tx.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                          {tx.channel}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`text-[9px] px-2 py-0.5 rounded font-bold ${
                            isFlagged
                              ? 'bg-rose-950 text-rose-400 border border-rose-500/50'
                              : 'bg-emerald-950 text-emerald-400 border border-emerald-500/50'
                          }`}
                        >
                          {tx.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button className="text-[10px] font-mono px-2 py-1 rounded bg-slate-800 hover:bg-cyber-accent hover:text-slate-950 text-slate-300 font-semibold transition-colors">
                          Trace Funds →
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Money Flow Inspection Drawer / Modal */}
      {selectedTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-4xl bg-cyber-surface border border-cyber-border rounded-xl shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-cyber-border">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-cyber-accent/10 border border-cyber-accent/30 flex items-center justify-center text-cyber-accent">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-mono text-sm font-bold text-slate-100 flex items-center gap-2">
                    MONEY-FLOW RECONSTRUCTION: {selectedTx.transaction_ref}
                  </h3>
                  <p className="text-xs text-slate-400 font-sans">
                    Origin: {selectedTx.sender_value} • Amount: ₹{selectedTx.amount.toLocaleString()}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSelectedTx(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Render MoneyFlowViewer */}
            <MoneyFlowViewer data={traceData} loading={loadingTrace} />

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedTx(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-semibold"
              >
                Close Trace View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
