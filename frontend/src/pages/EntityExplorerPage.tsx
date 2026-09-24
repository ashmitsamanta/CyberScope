import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Entity, EntityDetail, EntityType } from '../types';
import { RiskScoreBadge } from '../components/RiskScoreBadge';
import {
  Users,
  Search,
  Filter,
  Phone,
  Globe,
  CreditCard,
  Smartphone,
  Server,
  ArrowRight,
  ShieldAlert,
  Loader2,
  Calendar,
  Layers
} from 'lucide-react';

interface Props {
  onSelectCase?: (caseId: number) => void;
}

export const EntityExplorerPage: React.FC<Props> = ({ onSelectCase }) => {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selectedEntity, setSelectedEntity] = useState<EntityDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadEntities();
  }, [typeFilter]);

  const loadEntities = async () => {
    try {
      setLoading(true);
      const data = await api.getEntities({
        entity_type: typeFilter || undefined,
        search: searchTerm || undefined,
        limit: 80,
      });
      setEntities(data);
      if (data.length > 0 && !selectedEntity) {
        loadEntityDetail(data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadEntityDetail = async (id: number) => {
    try {
      setLoadingDetail(true);
      const detail = await api.getEntityDetail(id);
      setSelectedEntity(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const getEntityIcon = (type: EntityType) => {
    switch (type) {
      case 'PHONE': return Phone;
      case 'DOMAIN': return Globe;
      case 'UPI_ID':
      case 'BANK_ACCOUNT': return CreditCard;
      case 'DEVICE': return Smartphone;
      case 'IP_ADDRESS': return Server;
      default: return Users;
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
          <Users className="w-5 h-5 text-cyber-accent" />
          ENTITY INTEL EXPLORER
        </h1>
        <p className="text-xs text-slate-400 font-sans mt-0.5">
          Deterministic 360-degree profile for normalized phones, domains, payment handles, and bank accounts.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-cyber-surface border border-cyber-border flex flex-wrap items-center justify-between gap-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            loadEntities();
          }}
          className="flex items-center gap-2 flex-1 min-w-[280px]"
        >
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search phone, domain, UPI handle, or account..."
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
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyber-accent"
          >
            <option value="">All Entity Types</option>
            <option value="PHONE">Phone Numbers</option>
            <option value="DOMAIN">Domains</option>
            <option value="UPI_ID">UPI IDs</option>
            <option value="BANK_ACCOUNT">Bank Accounts</option>
            <option value="DEVICE">Devices</option>
            <option value="IP_ADDRESS">IP Addresses</option>
            <option value="PERSON">Persons</option>
          </select>
        </div>
      </div>

      {/* Two-Column Explorer Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left List (5 cols) */}
        <div className="lg:col-span-5 rounded-xl bg-cyber-surface border border-cyber-border overflow-hidden">
          <div className="p-3 bg-slate-900/80 border-b border-cyber-border flex justify-between items-center text-xs font-mono">
            <span className="text-slate-400 font-semibold">IDENTIFIERS ({entities.length})</span>
            <span className="text-[10px] text-slate-500">SORTED BY RISK</span>
          </div>

          <div className="max-h-[640px] overflow-y-auto divide-y divide-slate-800/80">
            {loading ? (
              <div className="p-16 flex flex-col items-center justify-center text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin text-cyber-accent mb-2" />
                <span className="text-xs font-mono">Loading entity database...</span>
              </div>
            ) : entities.map((ent) => {
              const Icon = getEntityIcon(ent.entity_type);
              const isSelected = selectedEntity?.id === ent.id;

              return (
                <div
                  key={ent.id}
                  onClick={() => loadEntityDetail(ent.id)}
                  className={`p-3.5 hover:bg-slate-900/90 cursor-pointer transition-colors flex items-center justify-between ${
                    isSelected ? 'bg-slate-900 border-l-2 border-cyber-accent' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-slate-800 flex items-center justify-center text-cyber-accent">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-mono text-xs font-bold text-slate-100 truncate max-w-[200px]">
                        {ent.value}
                      </div>
                      <div className="text-[10px] text-slate-400 uppercase font-sans">
                        {ent.entity_type}
                      </div>
                    </div>
                  </div>

                  <RiskScoreBadge score={ent.risk_score} size="sm" showLabel={false} />
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Detail Dossier (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {loadingDetail ? (
            <div className="p-20 flex flex-col items-center justify-center rounded-xl bg-cyber-surface border border-cyber-border text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-cyber-accent mb-3" />
              <p className="text-xs font-mono">Reconstructing entity relational profile...</p>
            </div>
          ) : selectedEntity ? (
            <div className="space-y-4">
              {/* Dossier Header Card */}
              <div className="p-5 rounded-xl bg-cyber-surface border border-cyber-border space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {selectedEntity.entity_type}
                    </span>
                    <h2 className="text-lg font-mono font-bold text-slate-100 mt-1 break-all">
                      {selectedEntity.value}
                    </h2>
                  </div>
                  <RiskScoreBadge score={selectedEntity.risk_score} size="lg" />
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">NORMALIZED</span>
                    <span className="text-slate-300 font-bold truncate block">{selectedEntity.normalized_value}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">LINKED CASES</span>
                    <span className="text-cyber-accent font-bold">{selectedEntity.connected_cases.length}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">RELATIONSHIPS</span>
                    <span className="text-slate-300 font-bold">{selectedEntity.neighbors.length}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">SENT VOLUME</span>
                    <span className="text-emerald-400 font-bold">₹{selectedEntity.transaction_summary.sent_volume.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Connected Cases */}
              <div className="p-4 rounded-xl bg-cyber-surface border border-cyber-border space-y-2.5">
                <h3 className="text-xs font-mono font-bold uppercase text-slate-200 flex items-center justify-between">
                  <span>INCIDENT ASSOCIATIONS ({selectedEntity.connected_cases.length})</span>
                  <span className="text-[10px] font-mono text-slate-400">TOUCHED CASES</span>
                </h3>

                {selectedEntity.connected_cases.length === 0 ? (
                  <p className="text-xs text-slate-500 font-mono py-2">
                    No explicit case filings referencing this synthetic entity directly.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {selectedEntity.connected_cases.map((c) => (
                      <div
                        key={c.id}
                        onClick={() => onSelectCase?.(c.id)}
                        className="p-3 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyber-accent cursor-pointer transition-colors flex items-center justify-between"
                      >
                        <div>
                          <div className="font-mono text-xs font-bold text-cyber-accent">{c.case_number}</div>
                          <div className="text-xs text-slate-300 font-medium">{c.title}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <RiskScoreBadge score={c.risk_score} size="sm" />
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Neighbors list */}
              <div className="p-4 rounded-xl bg-cyber-surface border border-cyber-border space-y-2.5">
                <h3 className="text-xs font-mono font-bold uppercase text-slate-200">
                  GRAPH NEIGHBOR HOPS ({selectedEntity.neighbors.length})
                </h3>
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {selectedEntity.neighbors.map((nb, i) => (
                    <div
                      key={i}
                      className="p-2 rounded bg-slate-900/60 border border-slate-800 text-xs font-mono flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-500 uppercase">[{nb.relationship_type}]</span>
                        <span className="text-slate-200 font-semibold">{nb.value}</span>
                      </div>
                      <span className="text-[10px] text-amber-400 font-bold">
                        {nb.risk_score} RISK
                      </span>
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
