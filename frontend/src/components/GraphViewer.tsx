import React, { useState, useRef, useMemo } from 'react';
import { GraphData, GraphNode, EntityType } from '../types';
import { ZoomIn, ZoomOut, RotateCcw, Filter, Maximize2, ShieldAlert } from 'lucide-react';

interface Props {
  data: GraphData;
  onSelectNode?: (node: GraphNode) => void;
  selectedNodeId?: string | null;
  height?: string;
  enableFilters?: boolean;
}

const ENTITY_COLORS: Record<string, { fill: string; stroke: string; text: string; glow: string }> = {
  PERSON: { fill: '#0284C7', stroke: '#38BDF8', text: '#E0F2FE', glow: 'rgba(56, 189, 248, 0.4)' },
  PHONE: { fill: '#E11D48', stroke: '#FB7185', text: '#FFE4E6', glow: 'rgba(251, 113, 133, 0.4)' },
  DOMAIN: { fill: '#7E22CE', stroke: '#C084FC', text: '#F3E8FF', glow: 'rgba(192, 132, 252, 0.4)' },
  URL: { fill: '#6B21A8', stroke: '#A855F7', text: '#F3E8FF', glow: 'rgba(168, 85, 247, 0.4)' },
  UPI_ID: { fill: '#D97706', stroke: '#FBBF24', text: '#FEF3C7', glow: 'rgba(251, 191, 36, 0.4)' },
  BANK_ACCOUNT: { fill: '#059669', stroke: '#34D399', text: '#D1FAE5', glow: 'rgba(52, 211, 153, 0.4)' },
  DEVICE: { fill: '#475569', stroke: '#94A3B8', text: '#F1F5F9', glow: 'rgba(148, 163, 184, 0.3)' },
  IP_ADDRESS: { fill: '#4338CA', stroke: '#818CF8', text: '#E0E7FF', glow: 'rgba(129, 140, 248, 0.4)' },
  CASE: { fill: '#BE123C', stroke: '#F43F5E', text: '#FFE4E6', glow: 'rgba(244, 63, 94, 0.6)' },
  DEFAULT: { fill: '#334155', stroke: '#64748B', text: '#F8FAFC', glow: 'rgba(100, 116, 139, 0.3)' },
};

export const GraphViewer: React.FC<Props> = ({
  data,
  onSelectNode,
  selectedNodeId,
  height = '500px',
  enableFilters = true,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [activeFilters, setActiveFilters] = useState<Record<string, boolean>>({
    PERSON: true,
    PHONE: true,
    DOMAIN: true,
    UPI_ID: true,
    BANK_ACCOUNT: true,
    CASE: true,
    DEVICE: true,
  });

  const svgRef = useRef<SVGSVGElement>(null);

  // Compute 2D node layout deterministically in a concentric/force circle
  const layoutNodes = useMemo(() => {
    if (!data.nodes || data.nodes.length === 0) return [];

    const width = 800;
    const heightSvg = 550;
    const centerX = width / 2;
    const centerY = heightSvg / 2;

    const filtered = data.nodes.filter(
      (n) => activeFilters[n.entity_type] !== false
    );

    // Group nodes into center hub vs satellite rings
    const highRiskOrCase = filtered.filter(
      (n) => n.risk_score >= 70 || n.entity_type === 'CASE' || n.entity_type === 'DOMAIN'
    );
    const others = filtered.filter(
      (n) => n.risk_score < 70 && n.entity_type !== 'CASE' && n.entity_type !== 'DOMAIN'
    );

    const positions: Array<GraphNode & { x: number; y: number }> = [];

    // Inner ring for high-risk / case anchors
    highRiskOrCase.forEach((node, i) => {
      const angle = (i / Math.max(1, highRiskOrCase.length)) * 2 * Math.PI;
      const radius = highRiskOrCase.length > 1 ? 130 : 0;
      positions.push({
        ...node,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      });
    });

    // Outer ring for secondary/peripheral entities
    others.forEach((node, i) => {
      const angle = (i / Math.max(1, others.length)) * 2 * Math.PI;
      const radius = 260 + (i % 2 === 0 ? 30 : -20);
      positions.push({
        ...node,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      });
    });

    return positions;
  }, [data.nodes, activeFilters]);

  const nodeMap = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    layoutNodes.forEach((n) => map.set(n.id, { x: n.x, y: n.y }));
    return map;
  }, [layoutNodes]);

  // Filter edges to only those with both visible endpoints
  const validEdges = useMemo(() => {
    if (!data.edges) return [];
    return data.edges.filter((e) => nodeMap.has(e.source) && nodeMap.has(e.target));
  }, [data.edges, nodeMap]);

  // Pan controls
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  const toggleFilter = (type: string) => {
    setActiveFilters((prev) => ({ ...prev, [type]: !prev[type] }));
  };

  return (
    <div className="relative w-full rounded-xl bg-[#090D18] border border-cyber-border overflow-hidden select-none" style={{ height }}>
      {/* Top Overlay Controls */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-2 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
        <span className="text-[11px] font-mono text-slate-400 mr-1 flex items-center gap-1">
          <Filter className="w-3 h-3 text-cyber-accent" /> Filter:
        </span>
        {enableFilters &&
          ['CASE', 'DOMAIN', 'PHONE', 'UPI_ID', 'BANK_ACCOUNT', 'PERSON'].map((type) => {
            const color = ENTITY_COLORS[type] || ENTITY_COLORS.DEFAULT;
            const isChecked = activeFilters[type] !== false;
            return (
              <button
                key={type}
                onClick={() => toggleFilter(type)}
                className={`px-2 py-0.5 rounded text-[10px] font-mono transition-all border ${
                  isChecked
                    ? 'border-opacity-60 bg-opacity-20 text-slate-200'
                    : 'opacity-40 border-slate-700 bg-transparent text-slate-500'
                }`}
                style={{
                  borderColor: color.stroke,
                  backgroundColor: isChecked ? color.fill + '33' : 'transparent',
                }}
              >
                {type}
              </button>
            );
          })}
      </div>

      {/* Zoom / Reset Controls */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1 bg-slate-950/80 backdrop-blur-md p-1 rounded-lg border border-slate-800">
        <button
          onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}
          className="p-1.5 hover:bg-slate-800 text-slate-300 rounded transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(0.4, z - 0.2))}
          className="p-1.5 hover:bg-slate-800 text-slate-300 rounded transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          className="p-1.5 hover:bg-slate-800 text-slate-300 rounded transition-colors"
          title="Reset View"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          {/* Arrow markers for directed edges */}
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="20"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569" />
          </marker>
          <marker
            id="arrow-flagged"
            viewBox="0 0 10 10"
            refX="22"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#F43F5E" />
          </marker>

          {/* Grid background pattern */}
          <pattern id="graph-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#162032" strokeWidth="0.8" />
          </pattern>
        </defs>

        <rect width="100%" height="100%" fill="url(#graph-grid)" />

        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {/* Edges */}
          {validEdges.map((edge) => {
            const src = nodeMap.get(edge.source)!;
            const tgt = nodeMap.get(edge.target)!;
            const isTransferred = edge.relationship_type === 'TRANSFERRED_TO';
            const strokeColor = isTransferred ? '#F43F5E' : '#334155';
            const strokeDash = edge.relationship_type === 'REPORTED_IN' ? '4,4' : 'none';

            // Midpoint for label
            const midX = (src.x + tgt.x) / 2;
            const midY = (src.y + tgt.y) / 2;

            return (
              <g key={edge.id} className="transition-opacity hover:opacity-100 opacity-70">
                <line
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke={strokeColor}
                  strokeWidth={isTransferred ? 2 : 1.2}
                  strokeDasharray={strokeDash}
                  markerEnd={isTransferred ? 'url(#arrow-flagged)' : 'url(#arrow)'}
                />
                {edge.amount ? (
                  <text
                    x={midX}
                    y={midY - 6}
                    fill="#FBBF24"
                    fontSize="9"
                    fontFamily="monospace"
                    textAnchor="middle"
                    className="pointer-events-none bg-slate-900 px-1 font-semibold"
                  >
                    ₹{edge.amount.toLocaleString()}
                  </text>
                ) : (
                  <text
                    x={midX}
                    y={midY - 4}
                    fill="#64748B"
                    fontSize="8"
                    fontFamily="monospace"
                    textAnchor="middle"
                    className="pointer-events-none"
                  >
                    {edge.relationship_type}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {layoutNodes.map((node) => {
            const isSelected = selectedNodeId === node.id || selectedNodeId === `e-${node.numeric_id}`;
            const color = ENTITY_COLORS[node.entity_type] || ENTITY_COLORS.DEFAULT;
            const isHighRisk = node.risk_score >= 70;
            const radius = node.entity_type === 'CASE' ? 22 : (isHighRisk ? 19 : 15);

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectNode?.(node);
                }}
                className="cursor-pointer group"
              >
                {/* Risk Glow halo */}
                {isHighRisk && (
                  <circle
                    r={radius + 8}
                    fill="none"
                    stroke={color.stroke}
                    strokeWidth="1.5"
                    strokeDasharray="3,3"
                    className="animate-spin opacity-40"
                    style={{ animationDuration: '10s' }}
                  />
                )}

                {/* Selection Ring */}
                {isSelected && (
                  <circle
                    r={radius + 5}
                    fill="none"
                    stroke="#06B6D4"
                    strokeWidth="2.5"
                    className="animate-pulse"
                  />
                )}

                {/* Node Body */}
                <circle
                  r={radius}
                  fill={color.fill}
                  stroke={color.stroke}
                  strokeWidth={isSelected ? 3 : 1.5}
                  className="transition-transform group-hover:scale-110"
                />

                {/* Risk Score Pill Indicator */}
                {node.risk_score > 0 && (
                  <rect
                    x={radius - 8}
                    y={-radius - 8}
                    width={22}
                    height={12}
                    rx="3"
                    fill={node.risk_score >= 70 ? '#E11D48' : '#D97706'}
                    className="pointer-events-none"
                  />
                )}
                {node.risk_score > 0 && (
                  <text
                    x={radius + 3}
                    y={-radius}
                    fill="#FFFFFF"
                    fontSize="8"
                    fontFamily="monospace"
                    fontWeight="bold"
                    textAnchor="middle"
                    className="pointer-events-none"
                  >
                    {Math.round(node.risk_score)}
                  </text>
                )}

                {/* Node Icon / Initial Letter */}
                <text
                  x="0"
                  y="4"
                  fill={color.text}
                  fontSize={radius > 16 ? '11' : '9'}
                  fontWeight="bold"
                  fontFamily="sans-serif"
                  textAnchor="middle"
                  className="pointer-events-none uppercase"
                >
                  {node.entity_type.charAt(0)}
                </text>

                {/* Label below node */}
                <text
                  x="0"
                  y={radius + 14}
                  fill="#E2E8F0"
                  fontSize="10"
                  fontFamily="monospace"
                  textAnchor="middle"
                  className="pointer-events-none drop-shadow group-hover:text-cyber-accent font-medium"
                >
                  {node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label}
                </text>

                {/* Sub-label Entity Type */}
                <text
                  x="0"
                  y={radius + 24}
                  fill="#94A3B8"
                  fontSize="8"
                  fontFamily="sans-serif"
                  textAnchor="middle"
                  className="pointer-events-none uppercase tracking-wider opacity-80"
                >
                  {node.entity_type}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Bottom stats ribbon */}
      <div className="absolute bottom-2 left-3 z-10 text-[10px] font-mono text-slate-500 bg-slate-950/70 px-2.5 py-1 rounded border border-slate-900">
        Entities: <span className="text-slate-300 font-semibold">{layoutNodes.length}</span> | Relationships: <span className="text-slate-300 font-semibold">{validEdges.length}</span> | Zoom: <span className="text-cyber-accent">{Math.round(zoom * 100)}%</span>
      </div>
    </div>
  );
};
