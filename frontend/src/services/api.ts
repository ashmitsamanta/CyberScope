import {
  DashboardStats,
  Case,
  CaseDetail,
  Entity,
  EntityDetail,
  Transaction,
  MoneyFlowTrace,
  GraphData,
  Campaign,
  CampaignDetail,
  TimelineEvent,
  InvestigationResponse
} from '../types';

const API_BASE = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.message || errorData.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Health
  getHealth: () => fetch(`${API_BASE}/health`).then(handleResponse<{ status: string }>),

  // Dashboard Stats
  getDashboardStats: (): Promise<DashboardStats> =>
    fetch(`${API_BASE}/stats/dashboard`).then(handleResponse<DashboardStats>),

  // Cases
  getCases: (params?: { status?: string; severity?: string; min_risk?: number; search?: string; limit?: number; offset?: number }): Promise<Case[]> => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.severity) searchParams.append('severity', params.severity);
    if (params?.min_risk !== undefined) searchParams.append('min_risk', params.min_risk.toString());
    if (params?.search) searchParams.append('search', params.search);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    return fetch(`${API_BASE}/cases?${searchParams.toString()}`).then(handleResponse<Case[]>);
  },

  getCaseDetail: (caseId: number): Promise<CaseDetail> =>
    fetch(`${API_BASE}/cases/${caseId}`).then(handleResponse<CaseDetail>),

  getCaseTimeline: (caseId: number): Promise<{ case_id: number; case_number: string; events: TimelineEvent[] }> =>
    fetch(`${API_BASE}/cases/${caseId}/timeline`).then(handleResponse<{ case_id: number; case_number: string; events: TimelineEvent[] }>),

  ingestReport: (payload: { title: string; content: string; channel?: string; sender_phone?: string }) =>
    fetch(`${API_BASE}/cases/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(handleResponse<any>),

  // Entities
  getEntities: (params?: { entity_type?: string; min_risk?: number; search?: string; limit?: number }): Promise<Entity[]> => {
    const searchParams = new URLSearchParams();
    if (params?.entity_type) searchParams.append('entity_type', params.entity_type);
    if (params?.min_risk !== undefined) searchParams.append('min_risk', params.min_risk.toString());
    if (params?.search) searchParams.append('search', params.search);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    return fetch(`${API_BASE}/entities?${searchParams.toString()}`).then(handleResponse<Entity[]>);
  },

  getEntityDetail: (entityId: number): Promise<EntityDetail> =>
    fetch(`${API_BASE}/entities/${entityId}`).then(handleResponse<EntityDetail>),

  // Transactions & Fund Tracing
  getTransactions: (params?: { channel?: string; min_amount?: number; case_id?: number; limit?: number }): Promise<Transaction[]> => {
    const searchParams = new URLSearchParams();
    if (params?.channel) searchParams.append('channel', params.channel);
    if (params?.min_amount !== undefined) searchParams.append('min_amount', params.min_amount.toString());
    if (params?.case_id !== undefined) searchParams.append('case_id', params.case_id.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    return fetch(`${API_BASE}/transactions?${searchParams.toString()}`).then(handleResponse<Transaction[]>);
  },

  traceMoneyFlow: (payload: { start_account_id?: number; start_transaction_id?: number; max_hops?: number }): Promise<MoneyFlowTrace> =>
    fetch(`${API_BASE}/transactions/trace-funds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(handleResponse<MoneyFlowTrace>),

  // Fraud Graph
  getGraph: (limit = 150): Promise<GraphData> =>
    fetch(`${API_BASE}/graph?limit=${limit}`).then(handleResponse<GraphData>),

  getCaseGraph: (caseId: number, hops = 2): Promise<GraphData> =>
    fetch(`${API_BASE}/graph/case/${caseId}?hops=${hops}`).then(handleResponse<GraphData>),

  getEntityNeighborhood: (entityId: number, hops = 2): Promise<GraphData> =>
    fetch(`${API_BASE}/graph/entity/${entityId}?hops=${hops}`).then(handleResponse<GraphData>),

  getShortestPath: (sourceId: number, targetId: number) =>
    fetch(`${API_BASE}/graph/shortest-path?source_id=${sourceId}&target_id=${targetId}`).then(handleResponse<any>),

  getSharedInfrastructure: () =>
    fetch(`${API_BASE}/graph/shared-infrastructure`).then(handleResponse<{ count: number; shared_infrastructure: any[] }>),

  getCircularFlows: () =>
    fetch(`${API_BASE}/graph/circular-flows`).then(handleResponse<{ cycles_count: number; cycles: any[] }>),

  // Campaigns
  getCampaigns: (): Promise<Campaign[]> =>
    fetch(`${API_BASE}/campaigns`).then(handleResponse<Campaign[]>),

  getCampaignDetail: (campaignIdOrCode: string | number): Promise<CampaignDetail> =>
    fetch(`${API_BASE}/campaigns/${campaignIdOrCode}`).then(handleResponse<CampaignDetail>),

  // CYBER-ASSIST AI Investigator
  queryCyberAssist: (payload: { query: string; case_id?: number | null; focus_entity_id?: number }): Promise<InvestigationResponse> =>
    fetch(`${API_BASE}/investigations/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(handleResponse<InvestigationResponse>),

  getCaseSummary: (caseId: number): Promise<InvestigationResponse> =>
    fetch(`${API_BASE}/investigations/summary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: caseId })
    }).then(handleResponse<InvestigationResponse>),

  // Natural Language Search
  searchNaturalLanguage: (q: string) =>
    fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`).then(handleResponse<any>),
};
