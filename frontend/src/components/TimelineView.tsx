import React from 'react';
import { TimelineEvent } from '../types';
import { MessageSquare, CreditCard, ShieldAlert, AlertCircle, FileText, ArrowRight } from 'lucide-react';

interface Props {
  events: TimelineEvent[];
}

export const TimelineView: React.FC<Props> = ({ events }) => {
  if (!events || events.length === 0) {
    return (
      <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl bg-cyber-card/30 text-slate-500 text-xs font-mono">
        No chronological timeline events logged for this incident file.
      </div>
    );
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'COMMUNICATION_RECEIVED':
        return { icon: MessageSquare, color: 'text-sky-400 bg-sky-950/80 border-sky-500/50' };
      case 'FINANCIAL_TRANSACTION':
        return { icon: CreditCard, color: 'text-amber-400 bg-amber-950/80 border-amber-500/50' };
      case 'INDICATOR_FLAGGED':
        return { icon: ShieldAlert, color: 'text-rose-400 bg-rose-950/80 border-rose-500/50' };
      default:
        return { icon: FileText, color: 'text-purple-400 bg-purple-950/80 border-purple-500/50' };
    }
  };

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
      {events.map((ev, idx) => {
        const { icon: Icon, color } = getEventIcon(ev.event_type);
        const dateStr = new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const fullDate = new Date(ev.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });

        return (
          <div key={ev.id || idx} className="relative group">
            {/* Timeline bullet dot */}
            <div
              className={`absolute -left-6 top-1 w-6 h-6 rounded-full border flex items-center justify-center ${color} shadow-sm z-10 transition-transform group-hover:scale-110`}
            >
              <Icon className="w-3 h-3" />
            </div>

            {/* Event Card */}
            <div className="bg-cyber-surface/90 border border-cyber-border rounded-xl p-3.5 hover:border-slate-600 transition-colors shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <span className="font-semibold text-xs text-slate-100 flex items-center gap-1.5 font-sans">
                  {ev.title}
                </span>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  {fullDate} {dateStr}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans mb-2">
                {ev.description}
              </p>

              {/* Linked Entities Chips */}
              {ev.entities && ev.entities.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1 border-t border-slate-800/80">
                  {ev.entities.map((ent, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900/90 text-slate-300 border border-slate-800"
                    >
                      <span className="text-slate-500 uppercase">{ent.type}:</span>
                      <span className="text-cyber-accent font-medium">{ent.value}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
