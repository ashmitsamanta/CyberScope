import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { GraphData, GraphNode } from '../types';
import { GraphViewer } from '../components/GraphViewer';
import { RiskScoreBadge } from '../components/RiskScoreBadge';
import {
  Share2,
  Search,
  Filter,
  Layers,
  Repeat,
  ShieldAlert,
  Loader2,
  ExternalLink,
  ChevronRight,
  Info
} from 'lucide-react';

interface Props {
  onSelectCase?: (caseId: number) => void;
}

export const GraphPage: React.FC<Props> = ({ onSelectCase }) => {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedNodeDetails, setSelectedNodeDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [sharedInfraList, setSharedInfraList] = useState<any[]>([]);
  const [showSharedOnly, setShowSharedOnly] = useState(false);

  useEffect(() => {
    loadGraph();
    loadSharedInfra();
  }, []);

  const loadGraph = async () => {
    try {
      setLoading(true);
      const data = await api.getGraph(120);
      setGraphData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadSharedInfra = async () => {
    try {
      const res = await api.getSharedInfrastructure();
      setSharedInfraList(res.shared_infrastructure || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectNode = async (node: GraphNode) => {
    setSelectedNode(node);
    try {
      setLoadingDetails(true);
      const detail = await api.getEntityDetail(node.numeric_id);
      setSelectedNodeDetails(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleHopExpand = async (hops: number) => {
    if (!selectedNode) return;
    try {
      setLoading(true);
      const expanded = await api.getEntityNeighborhood(selectedNode.numeric_id, hops);
      setGraphData(expanded);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDetectCircular = async () => {
    try {
      setLoading(true);
      const res = await api.getCircularFlows();
      if (res.cycles && res.cycles.length > 0) {
        // Highlighting nodes in cycles
        const cycleNodeIds = new Set();
        res.cycles.forEach((c: any) => c.cycle.forEach((nid: string) => cycleNodeIds.add(nid)));
        const filteredNodes = graphData.nodes.filter((n) => cycleNodeIds.has(n.id));
        if (filteredNodes.length > 0) {
          setSelectedNode(filteredNodes[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2">
            <Share2 className="w-5 h-5 text-cyber-accent" />
            INTERACTIVE FRAUD GRAPH EXPLORER
          </h1>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Visualize multi-hop connections, identify common nexus nodes, and detect fund cycles.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleDetectCircular}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono flex items-center gap-1.5 transition-colors"
          >
            <Repeat className="w-3.5 h-3.5 text-amber-400" />
            Detect Fund Cycles
          </button>
          <button
            onClick={loadGraph}
            className="px-3 py-1.5 rounded-lg bg-cyber-accent hover:bg-cyber-accentHover text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-colors"
          >
            Reload Full Network
          </button>
        </div>
      </div>

      {/* Main Split: Large Graph Canvas (8 cols) + Node Inspector / Shared Hubs (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Graph Canvas */}
        <div className="lg:col-span-8 flex flex-col space-y-3">
          {loading ? (
            <div className="h-[600px] flex flex-col items-center justify-center rounded-xl bg-cyber-surface border border-cyber-border text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-cyber-accent mb-3" />
              <p className="text-xs font-mono">Computing topological layout and resolving entity coordinates...</p>
            </div>
          ) : (
            <GraphViewer
              data={graphData}
              height="600px"
              selectedNodeId={selectedNode?.id}
              onSelectNode={handleSelectNode}
              enableFilters={true}
            />
          )}

          {/* Quick Hop Expansion Toolbar */}
          {selectedNode && (
            <div className="p-3 rounded-xl bg-slate-900 border border-cyber-border flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Active Node:</span>
                <span className="text-cyber-accent font-bold">{selectedNode.label}</span>
                <span className="text-[10px] text-slate-500 uppercase">({selectedNode.entity_type})</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400 text-[11px]">Expand Neighborhood:</span>
                <button
                  onClick={() => handleHopExpand(1)}
                  className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                >
                  1-Hop
                </button>
                <button
                  onClick={() => handleHopExpand(2)}
                  className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                >
                  2-Hops
                </button>
                <button
                  onClick={() => handleHopExpand(3)}
                  className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                >
                  3-Hops
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar: Node Inspector / Shared Hubs */}
        <div className="lg:col-span-4 space-y-6">
          {/* Node Inspector */}
          <div className="p-4 rounded-xl bg-cyber-surface border border-cyber-border space-y-3">
            <h3 className="text-xs font-mono font-bold uppercase text-slate-200 flex items-center justify-between">
              <span>ENTITY INSPECTOR</span>
              {selectedNode && <RiskScoreBadge score={selectedNode.risk_score} size="sm" />}
            </h3>

            {selectedNode ? (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">{selectedNode.entity_type}</div>
                  <div className="text-sm font-mono font-bold text-slate-100 break-all">{selectedNode.label}</div>
                </div>

                {loadingDetails ? (
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-400 py-3">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-cyber-accent" />
                    Fetching entity dossier...
                  </div>
                ) : selectedNodeDetails ? (
                  <div className="space-y-3 text-xs">
                    {/* Connected Cases */}
                    <div>
                      <div className="text-[10px] font-mono text-slate-400 mb-1">
                        LINKED INCIDENT CASES ({selectedNodeDetails.connected_cases?.length || 0})
                      </div>
                      <div className="space-y-1.5 max-h-32 overflow-y-auto">
                        {selectedNodeDetails.connected_cases?.map((c: any) => (
                          <div
                            key={c.id}
                            onClick={() => onSelectCase?.(c.id)}
                            className="p-2 rounded bg-slate-900/80 hover:bg-slate-800 border border-slate-800 flex items-center justify-between cursor-pointer group"
                          >
                            <span className="font-mono text-cyber-accent font-semibold">{c.case_number}</span>
                            <span className="text-[10px] text-slate-400 group-hover:text-slate-200 flex items-center gap-1">
                              Open <ChevronRight className="w-3 h-3" />
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Neighbors list */}
                    <div>
                      <div className="text-[10px] font-mono text-slate-400 mb-1">
                        NEIGHBOR RELATIONS ({selectedNodeDetails.neighbors?.length || 0})
                      </div>
                      <div className="space-y-1 max-h-40 overflow-y-auto font-mono text-[11px]">
                        {selectedNodeDetails.neighbors?.map((nb: any, i: number) => (
                          <div key={i} className="p-1.5 rounded bg-slate-900/50 flex items-center justify-between text-slate-300">
                            <span className="truncate max-w-[140px] text-slate-200">{nb.value}</span>
                            <span className="text-[9px] text-slate-500 uppercase">{nb.relationship_type}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="p-8 text-center text-xs font-mono text-slate-500">
                Click any node in the graph above to inspect connected cases, risk score, and neighboring hops.
              </div>
            )}
          </div>

          {/* Shared Infrastructure Ranking */}
          <div className="p-4 rounded-xl bg-cyber-surface border border-cyber-border space-y-3">
            <h3 className="text-xs font-mono font-bold uppercase text-slate-200 flex items-center justify-between">
              <span>SHARED SYNDICATE INFRASTRUCTURE</span>
              <span className="text-[10px] font-mono text-cyber-accent">{sharedInfraList.length} HUBS</span>
            </h3>

            <div className="space-y-2 max-h-60 overflow-y-auto">
              {sharedInfraList.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    const match = graphData.nodes.find((n) => n.id === item.node_id);
                    if (match) handleSelectNode(match);
                  }}
                  className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-cyber-accent/60 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="font-bold text-slate-100 truncate max-w-[170px]">{item.value}</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-500/40">
                      {item.connected_case_count} CASES
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-sans">
                    Shared by: {item.connected_cases.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
