import { ChatActions } from "../../../types/apiContracts";

export const ACTION_LABELS = {
  [ChatActions.autoReply]: "自动解决",
  [ChatActions.handoff]: "转人工",
  [ChatActions.createTicket]: "建工单",
};

export const RISK_LABELS = {
  low: "低",
  medium: "中",
  high: "高",
};

export const INTENT_LABELS = {
  logistics_question: "物流/进度问题",
  return_refund: "退款/费用问题",
  exchange_after_sale: "更换/服务处理",
  invoice_question: "票据/账务问题",
  product_damage: "异常/损坏问题",
  complaint_risk: "投诉/升级风险",
  unknown: "未知问题",
};

export const PRIORITY_LABELS = {
  P0: "紧急",
  P1: "高",
  P2: "中",
  P3: "低",
};

export const QUEUE_STATUS_LABELS = {
  pending: "待接管",
  in_progress: "处理中",
  resolved: "已处理",
  ticket_created: "已转工单",
};

export const TICKET_STATUS_LABELS = {
  Open: "新建",
  "In Progress": "处理中",
  Pending: "待客户确认",
  Waiting: "待客户确认",
  "Pending Customer": "待客户确认",
  Resolved: "已完成",
  Closed: "已完成",
};

export const WORKFLOW_STEP_STATUS_LABELS = {
  running: "执行中",
  completed: "已完成",
  pending: "待执行",
  failed: "失败",
};

export function normalizeTrace(trace) {
  const intent = trace.intent?.intent ?? "unknown";
  const risk = trace.risk?.risk_level ?? "low";
  const action = trace.action ?? ChatActions.autoReply;

  return {
    id: trace.trace_id,
    customerId: trace.customer_id,
    message: trace.message,
    issueType: INTENT_LABELS[intent] ?? intent,
    riskLevel: risk,
    riskLabel: RISK_LABELS[risk] ?? risk,
    riskReason: trace.risk?.reason ?? "",
    action,
    actionLabel: ACTION_LABELS[action] ?? action,
    elapsedMs: trace.elapsed_ms ?? 0,
    ticketId: trace.ticket?.ticket_id ?? "",
    ticketStatus: trace.ticket?.status ?? "",
    assignee: trace.ticket?.assignee ?? "",
    answer: trace.answer ?? "",
    citations: trace.citations ?? [],
    createdAt: trace.created_at ?? "",
    raw: trace,
  };
}

export function summarizeTraces(rows) {
  const total = rows.length;
  const handoff = rows.filter((row) => row.action === ChatActions.handoff).length;
  const tickets = rows.filter((row) => row.action === ChatActions.createTicket).length;
  const highRisk = rows.filter((row) => row.riskLevel === "high").length;

  return { total, handoff, tickets, highRisk };
}
