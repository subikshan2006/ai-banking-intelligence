const API_BASE = "http://localhost:8000/api";

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {})
    },
    ...options
  });
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const err = await res.json();
      errorDetail = err.detail || JSON.stringify(err);
    } catch (_) {}
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => fetchJson<any>("/dashboard/summary"),

  // Customers
  getCustomers: (search?: string, limit = 20, offset = 0) => {
    const q = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (search) q.append("search", search);
    return fetchJson<{ total: number; customers: any[] }>(`/customers?${q}`);
  },
  getCustomerDetails: (customerId: string) => fetchJson<any>(`/customers/${customerId}`),
  getCustomerAccounts: (customerId: string) => fetchJson<any[]>(`/customers/${customerId}/accounts`),

  // Transactions
  getTransactions: (params?: { customer_id?: string; category?: string; status?: string; is_flagged?: boolean; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.customer_id) q.append("customer_id", params.customer_id);
    if (params?.category) q.append("category", params.category);
    if (params?.status) q.append("status", params.status);
    if (params?.is_flagged !== undefined) q.append("is_flagged", String(params.is_flagged));
    if (params?.limit) q.append("limit", String(params.limit));
    return fetchJson<{ total: number; transactions: any[] }>(`/transactions?${q}`);
  },
  getTransactionDetails: (id: string) => fetchJson<any>(`/transactions/${id}`),

  // Fraud
  getFraudAlerts: (riskLevel?: string, status?: string) => {
    const q = new URLSearchParams();
    if (riskLevel) q.append("risk_level", riskLevel);
    if (status) q.append("status", status);
    return fetchJson<{ total: number; alerts: any[] }>(`/fraud/alerts?${q}`);
  },
  analyzeTransaction: (payload: { transaction_id?: string; amount?: number; customer_id?: string }) =>
    fetchJson<any>("/fraud/analyze", { method: "POST", body: JSON.stringify(payload) }),
  explainTransactionRisk: (txId: string) => fetchJson<any>(`/fraud/transaction/${txId}`),

  // Loans
  getLoans: (customerId?: string, approvalStatus?: string) => {
    const q = new URLSearchParams();
    if (customerId) q.append("customer_id", customerId);
    if (approvalStatus) q.append("approval_status", approvalStatus);
    return fetchJson<any[]>(`/loans?${q}`);
  },
  evaluateLoan: (payload: { customer_id: string; requested_amount: number; tenure_months: number; purpose?: string }) =>
    fetchJson<any>("/loans/evaluate", { method: "POST", body: JSON.stringify(payload) }),
  compareLoans: (scenarios: Array<{ principal: number; tenure_months: number; interest_rate: number }>) =>
    fetchJson<any>("/loans/compare", { method: "POST", body: JSON.stringify({ scenarios }) }),
  calculateEmi: (scenario: { principal: number; tenure_months: number; interest_rate: number }) =>
    fetchJson<any>("/loans/calculate-emi", { method: "POST", body: JSON.stringify(scenario) }),

  // Assistant Chat
  sendChatMessage: (message: string, demoRole = "manager") =>
    fetchJson<any>("/assistant/chat", {
      method: "POST",
      body: JSON.stringify({ message, demo_role: demoRole })
    }),
  getTrace: (correlationId: string) => fetchJson<any[]>(`/assistant/traces/${correlationId}`),

  // Agents & Tools
  getAgentsStatus: () => fetchJson<any>("/agents/status"),
  getTools: () => fetchJson<any>("/agents/tools"),

  // Approvals
  getApprovals: (status?: string) => {
    const q = new URLSearchParams();
    if (status) q.append("status", status);
    return fetchJson<{ total: number; approvals: any[] }>(`/approvals?${q}`);
  },
  approveRequest: (id: string, decisionReason: string, approverRole = "compliance_manager") =>
    fetchJson<any>(`/approvals/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ decision: "APPROVED", decision_reason: decisionReason, approver_role: approverRole })
    }),
  rejectRequest: (id: string, decisionReason: string, approverRole = "compliance_manager") =>
    fetchJson<any>(`/approvals/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ decision: "REJECTED", decision_reason: decisionReason, approver_role: approverRole })
    }),

  // Investigations
  getInvestigations: () => fetchJson<any[]>("/investigations"),
  getInvestigationDetails: (id: string) => fetchJson<any>(`/investigations/${id}`),
  createInvestigation: (customerId: string) =>
    fetchJson<any>(`/investigations?customer_id=${customerId}`, { method: "POST" }),

  // Knowledge / Policies
  searchKnowledge: (query: string) => fetchJson<any>(`/knowledge/search?query=${encodeURIComponent(query)}`),
  getPolicies: () => fetchJson<any[]>("/knowledge/policies"),
  getPolicyDetails: (id: string) => fetchJson<any>(`/knowledge/policies/${id}`),

  // Simulator
  getSimulatorStatus: () => fetchJson<any>("/simulator/status"),
  startSimulator: () => fetchJson<any>("/simulator/start", { method: "POST" }),
  stopSimulator: () => fetchJson<any>("/simulator/stop", { method: "POST" }),
  generateTransaction: (forceSuspicious = false) =>
    fetchJson<any>("/simulator/generate", {
      method: "POST",
      body: JSON.stringify({ force_suspicious: forceSuspicious })
    }),

  // Audit
  getAuditLogs: (correlationId?: string, actor?: string, limit = 50) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (correlationId) q.append("correlation_id", correlationId);
    if (actor) q.append("actor", actor);
    return fetchJson<{ count: number; logs: any[] }>(`/audit/logs?${q}`);
  },

  // Notifications
  getNotifications: (unreadOnly = false) =>
    fetchJson<any[]>(`/notifications?unread_only=${unreadOnly}`),
  markNotificationRead: (id: string) =>
    fetchJson<any>(`/notifications/${id}/read`, { method: "POST" }),

  // Evaluation
  getEvaluationRuns: () => fetchJson<any[]>("/evaluation/runs"),
  runEvaluation: () => fetchJson<any>("/evaluation/run", { method: "POST" })
};
