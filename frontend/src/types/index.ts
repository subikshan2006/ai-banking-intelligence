export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  kyc_status: string;
  risk_rating: string;
  monthly_income: number;
  existing_monthly_debt?: number;
  employer: string;
  city: string;
  created_at: string;
}

export interface Account {
  id: string;
  customer_id?: string;
  account_number?: string;
  masked_account_number: string;
  account_type: string;
  balance: number;
  currency: string;
  status: string;
}

export interface Transaction {
  id: string;
  account_id: string;
  customer_id: string;
  amount: number;
  txn_type: string;
  category: string;
  merchant_name: string;
  location?: string;
  status: string;
  timestamp: string;
  is_flagged: boolean;
  description?: string;
}

export interface SpendingCategory {
  category: string;
  total_amount: number;
  transaction_count: number;
  percentage: number;
}

export interface SpendingSummary {
  customer_id: string;
  period_days: number;
  transaction_count: number;
  total_inflow: number;
  total_outflow: number;
  net_cashflow: number;
  categories: SpendingCategory[];
}

export interface RuleHit {
  rule_name: string;
  condition: string;
  threshold: any;
  observed_value: any;
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface MLAnomalyOutput {
  model_name: string;
  is_anomaly: boolean;
  raw_anomaly_score: number;
  contamination_threshold: number;
  features_used: string[];
  disclaimer: string;
}

export interface FraudAlert {
  id: string;
  transaction_id: string;
  customer_id: string;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  triggered_rules: string[];
  anomaly_score: number;
  is_ml_anomaly: boolean;
  evidence?: any;
  recommended_action: string;
  status: string;
  created_at: string;
}

export interface LoanApplication {
  id: string;
  customer_id: string;
  requested_amount: number;
  tenure_months: number;
  purpose: string;
  interest_rate: number;
  estimated_emi: number;
  dti_ratio: number;
  assessment_result: string;
  approval_status: string;
  assessment_notes: string;
  created_at: string;
}

export interface LoanScenario {
  scenario_id: string;
  principal: number;
  tenure_months: number;
  interest_rate: number;
  monthly_emi: number;
  total_repayment: number;
  total_interest: number;
}

export interface ApprovalRequest {
  id: string;
  request_id: string;
  agent_name: string;
  action_type: string;
  payload: any;
  payload_hash: string;
  idempotency_key: string;
  risk_level: string;
  reason: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";
  decision_by?: string;
  decision_reason?: string;
  decision_at?: string;
  execution_result?: any;
  expires_at: string;
  created_at: string;
}

export interface ToolCallRecord {
  tool_name: string;
  arguments: any;
  output: any;
  duration_ms: number;
  status: "success" | "error";
  error?: string;
}

export interface ExecutionTraceItem {
  step_id: string;
  phase: string;
  agent_name?: string;
  tool_name?: string;
  input_data?: any;
  output_data?: any;
  status: string;
  duration_ms: number;
  timestamp: string;
}

export interface ChatResponse {
  correlation_id: string;
  intent: string;
  execution_mode: "deterministic_fallback" | "llm";
  status: "completed" | "failed" | "clarification_needed";
  answer: string;
  agents_involved: string[];
  tool_results: ToolCallRecord[];
  trace: ExecutionTraceItem[];
  errors: string[];
  structured_data: any;
}

export interface PolicyDocument {
  id: string;
  title: string;
  category: string;
  version: string;
  effective_date: string;
  content?: string;
  passages?: Array<{ id: string; text: string }>;
  passages_count?: number;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "INFO" | "WARNING" | "ALERT" | "SUCCESS";
  is_read: boolean;
  link_url?: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  correlation_id: string;
  timestamp: string;
  actor: string;
  event_type: string;
  tool_name?: string;
  details: string;
  duration_ms: number;
  status: string;
}

export interface EvaluationCase {
  case_id: string;
  prompt: string;
  expected_intent: string;
  actual_intent: string;
  expected_agents: string[];
  actual_agents: string[];
  status: "PASSED" | "FAILED";
  grounded: boolean;
  execution_time_ms: number;
  details: string;
}

export interface EvaluationResponse {
  evaluation_id: string;
  timestamp: string;
  total_cases: number;
  passed_cases: number;
  accuracy_rate: number;
  mode: string;
  results: EvaluationCase[];
}

export interface DashboardMetrics {
  total_customers: number;
  active_accounts: number;
  total_transaction_volume: number;
  total_transactions_count: number;
  open_fraud_alerts: number;
  total_fraud_alerts: number;
  pending_approvals: number;
  total_loans: number;
  agent_executions_count: number;
  is_simulator_running: boolean;
}
