import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Campaign, CampaignDetail } from '../types';
import { RiskScoreBadge } from '../components/RiskScoreBadge';
import {
  Target,
  FolderGit2,
  Share2,
  Calendar,
  ShieldAlert,
  Loader2,
  ExternalLink,
  ChevronRight,
  Globe,
  Phone,
  CreditCard,
  Layers
} from 'lucide-react';

interface Props {
  onSelectCase?: (caseId: number) => void;
}

export const CampaignsPage: React.FC<Props> = ({ onSelectCase }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCamp, setSelectedCamp] = useState<CampaignDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const data = await api.getCampaigns();
      setCampaigns(data);
      if (data.length > 0) {
        loadCampaignDetail(data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCampaignDetail = async (id: number) => {
    try {
      setLoadingDetail(true);
      const detail = await api.getCampaignDetail(id);
      setSelectedCamp(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetail(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
          <Target className="w-5 h-5 text-purple-400" />
          COORDINATED FRAUD CAMPAIGN CLUSTERS
        </h1>
        <p className="text-xs text-slate-400 font-sans mt-0.5">
          Detect and aggregate multi-victim fraud rings sharing command domains, payment handles, and telephony infrastructure.
        </p>
      </div>

      {/* Main Grid: Campaign Cards List + Selected Campaign Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Campaigns List (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="text-xs font-mono text-slate-400 font-semibold uppercase px-1">
            ACTIVE THREAT CAMPAIGNS ({campaigns.length})
          </div>

          {loading ? (
            <div className="p-16 flex flex-col items-center justify-center rounded-xl bg-cyber-surface border border-cyber-border text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin text-cyber-accent mb-2" />
              <span className="text-xs font-mono">Correlating shared infrastructure clusters...</span>
            </div>
          ) : (
            <div className="space-y-3">
              {campaigns.map((camp) => {
                const isSelected = selectedCamp?.id === camp.id;
                const isPrimary = camp.campaign_id === 'CAMP-PHANTOM-KYC';

                return (
                  <div
                    key={camp.id}
                    onClick={() => loadCampaignDetail(camp.id)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer shadow-sm ${
                      isSelected
                        ? 'bg-purple-950/20 border-purple-500/70 shadow-[0_0_15px_rgba(168,85,247,0.15)]'
                        : 'bg-cyber-surface border-cyber-border hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="font-mono text-xs font-bold text-slate-100 flex items-center gap-2">
                        {camp.name}
                        {isPrimary && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-900/60 text-purple-300 border border-purple-500/40">
                            DEMO SYNDICATE
                          </span>
                        )}
                      </span>
                      <RiskScoreBadge score={camp.risk_score} size="sm" />
                    </div>

                    <p className="text-xs text-slate-400 line-clamp-2 font-sans mb-3 leading-relaxed">
                      {camp.description}
                    </p>

                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-500">
                      <div className="flex items-center gap-3">
                        <span>CASES: <strong className="text-slate-200">{camp.case_count}</strong></span>
                        <span>ENTITIES: <strong className="text-slate-200">{camp.entity_count}</strong></span>
                      </div>
                      <span className="text-purple-400 font-semibold flex items-center gap-1">
                        View Dossier <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Selected Campaign Deep Dive (7 cols) */}
        <div className="lg:col-span-7">
          {loadingDetail ? (
            <div className="p-24 flex flex-col items-center justify-center rounded-xl bg-cyber-surface border border-cyber-border text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-cyber-accent mb-3" />
              <p className="text-xs font-mono">Compiling campaign telemetry and cross-case evidence...</p>
            </div>
          ) : selectedCamp ? (
            <div className="space-y-4">
              {/* Campaign Header Banner */}
              <div className="p-5 rounded-xl bg-cyber-surface border border-cyber-border space-y-3 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-500/40">
                      CAMPAIGN CLUSTER: {selectedCamp.campaign_id}
                    </span>
                    <h2 className="text-lg font-mono font-bold text-slate-100 mt-1">
                      {selectedCamp.name}
                    </h2>
                  </div>
                  <RiskScoreBadge score={selectedCamp.risk_score} size="lg" />
                </div>

                <p className="text-xs text-slate-300 font-sans leading-relaxed">
                  {selectedCamp.description}
                </p>

                {/* Shared Indicators Matrix */}
                {selectedCamp.shared_indicators && (
                  <div className="pt-3 border-t border-slate-800 space-y-2">
                    <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold block">
                      SHARED INFRASTRUCTURE FINGERPRINTS
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                      {selectedCamp.shared_indicators.domains && (
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          <span className="text-[10px] text-purple-400 font-bold block mb-1 flex items-center gap-1">
                            <Globe className="w-3 h-3" /> COMMAND DOMAINS
                          </span>
                          <div className="space-y-0.5 text-slate-200">
                            {selectedCamp.shared_indicators.domains.map((d: string, i: number) => (
                              <div key={i} className="truncate">• {d}</div>
                            ))}
                          </div>
                        </div>
                      )}

                      {selectedCamp.shared_indicators.upi_ids && (
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          <span className="text-[10px] text-amber-400 font-bold block mb-1 flex items-center gap-1">
                            <CreditCard className="w-3 h-3" /> PAYMENT HANDLES
                          </span>
                          <div className="space-y-0.5 text-slate-200">
                            {selectedCamp.shared_indicators.upi_ids.map((u: string, i: number) => (
                              <div key={i} className="truncate">• {u}</div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Linked Incident Cases */}
              <div className="p-4 rounded-xl bg-cyber-surface border border-cyber-border space-y-3">
                <h3 className="text-xs font-mono font-bold uppercase text-slate-200 flex items-center justify-between">
                  <span>CONNECTED INCIDENT FILES ({selectedCamp.cases?.length || 0})</span>
                  <span className="text-[10px] font-mono text-slate-400">1-CLICK INVESTIGATION</span>
                </h3>

                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {selectedCamp.cases?.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => onSelectCase?.(c.id)}
                      className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-cyber-accent cursor-pointer transition-colors flex items-center justify-between group"
                    >
                      <div>
                        <div className="font-mono text-xs font-bold text-cyber-accent group-hover:text-cyan-300">
                          {c.case_number}
                        </div>
                        <div className="text-xs text-slate-300 font-sans font-medium line-clamp-1">
                          {c.title}
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <RiskScoreBadge score={c.risk_score} size="sm" />
                        <span className="text-[11px] font-mono text-slate-400 group-hover:text-slate-200 flex items-center gap-1">
                          Open <ChevronRight className="w-3.5 h-3.5" />
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
