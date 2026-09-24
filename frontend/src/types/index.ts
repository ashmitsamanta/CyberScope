export interface RiskSignal {
  code: string;
  points: number;
  explanation: string;
  category?: string;
}

export interface Case {
  id: number;
  case_number: string;
  title: string;
  description: string;
  status: 'NEW' | 'INVESTIGATING' | 'ESCALATED' | 'RESOLVED' | 'FALSE_POSITIVE';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  source: string;
  risk_score: number;
  campaign_id?: number | null;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface CaseDetail extends Case {
  risk_breakdown: {
    score: number;
    level: string;
    signals: RiskSignal[];
    summary: string;
  };
  transaction_count: number;
  message_count: number;
  indicator_count: number;
  campaign_name?: string | null;
}

export type EntityType = 
  | 'PERSON'
  | 'PHONE'
  | 'EMAIL'
  | 'URL'
  | 'DOMAIN'
  | 'UPI_ID'
  | 'BANK_ACCOUNT'
  | 'DEVICE'
  | 'IP_ADDRESS'
  | 'MERCHANT'
  | 'ORGANIZATION'
  | 'CASE';

export interface Entity {
  id: number;
  entity_type: EntityType;
  value: string;
  normalized_value: string;
  risk_score: number;
  first_seen?: string;
  last_seen?: string;
  metadata?: Record<string, any>;
}

export interface EntityNeighbor {
  id: number;
  entity_type: EntityType;
  value: string;
  normalized_value: string;
  risk_score: number;
  relationship_type: string;
  confidence: number;
  direction: 'outgoing' | 'incoming';
}

export interface EntityDetail extends Entity {
  connected_cases: Array<{
    id: number;
    case_number: string;
    title: string;
    status: string;
    severity: string;
    risk_score: number;
  }>;
  neighbors: EntityNeighbor[];
  transaction_summary: {
    sent_count: number;
    sent_volume: number;
    received_count: number;
    received_volume: number;
  };
  indicators: Array<{
    id: number;
    indicator_type: string;
    severity: string;
    description: string;
    detected_at: string;
  }>;
}

export interface Transaction {
  id: number;
  transaction_ref: string;
  timestamp: string;
  sender_entity_id: number;
  receiver_entity_id: number;
  amount: number;
  currency: string;
  channel: string;
  status: string;
  sender_value?: string;
  receiver_value?: string;
  sender_type?: EntityType;
  receiver_type?: EntityType;
  case_number?: string;
  risk_signals?: RiskSignal[];
  metadata?: Record<string, any>;
}

export interface MoneyFlowNode {
  id: string;
  entity_id: number;
  label: string;
  entity_type: string;
  risk_score: number;
  hop_level: number;
  role: 'SOURCE' | 'INTERMEDIARY' | 'DESTINATION' | 'MULE';
}

export interface MoneyFlowEdge {
  id: string;
  source: string;
  target: string;
  amount: number;
  currency: string;
  channel: string;
  timestamp: string;
  transaction_ref: string;
  flagged: boolean;
}

export interface MoneyFlowTrace {
  root_entity_id: number;
  max_hops_reached: number;
  total_volume_traced: number;
  detected_patterns: Array<{
    pattern: string;
    explanation: string;
    amount?: number;
    entity_id?: number;
  }>;
  nodes: MoneyFlowNode[];
  edges: MoneyFlowEdge[];
  summary: string;
}

export interface GraphNode {
  id: string;
  numeric_id: number;
  label: string;
  entity_type: EntityType;
  risk_score: number;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  confidence: number;
  amount?: number;
  metadata?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats?: Record<string, any>;
}

export interface Campaign {
  id: number;
  campaign_id: string;
  name: string;
  description: string;
  risk_score: number;
  case_count: number;
  entity_count: number;
  status: string;
  first_seen?: string;
  last_seen?: string;
  shared_indicators?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface CampaignDetail extends Campaign {
  cases: Case[];
  key_entities: Entity[];
  timeline: Array<{
    date: string;
    title: string;
    description: string;
  }>;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  event_type: string;
  title: string;
  description: string;
  severity: string;
  entities: Array<{ type: string; value: string }>;
  metadata: Record<string, any>;
}

export interface EvidenceCitation {
  tag: string;
  type: string;
  identifier: string;
  summary: string;
}

export interface InvestigationResponse {
  query: string;
  case_id?: number | null;
  answer: string;
  observed_evidence: string[];
  calculated_signals: RiskSignal[];
  inferences: string[];
  uncertainties: string[];
  evidence_citations: EvidenceCitation[];
  recommended_next_steps: string[];
  model_used: string;
}

export interface DashboardStats {
  kpis: {
    total_cases: number;
    high_risk_cases: number;
    critical_cases: number;
    linked_entities: number;
    detected_campaigns: number;
    transactions_analyzed: number;
    total_volume_analyzed: number;
  };
  risk_distribution: Array<{ level: string; count: number; color: string }>;
  entity_distribution: Array<{ type: string; count: number }>;
  recent_high_risk_cases: Case[];
  active_campaigns: Campaign[];
}
