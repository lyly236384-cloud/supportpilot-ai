export const ApiPaths = {
  chat: "/api/chat",
  chatStream: "/api/chat/stream",
  productChat: "/api/product-chat",
  knowledgeDocuments: "/api/knowledge/documents",
  knowledgeImport: "/api/knowledge/documents/import",
  knowledgeReindex: "/api/knowledge/reindex",
  metrics: "/api/metrics",
  metricsRebuild: "/api/metrics/rebuild",
  metricsTrends: "/api/metrics/trends",
  queue: "/api/queue",
  tickets: "/api/tickets",
  traces: "/api/traces",
  tracesExport: "/api/traces/export",
  seed: "/api/seed",
  customers: "/api/customers",
};

export const ChatActions = {
  autoReply: "auto_reply",
  handoff: "handoff",
  createTicket: "create_ticket",
};

export function getKnowledgeDocumentPath(documentId) {
  return `${ApiPaths.knowledgeDocuments}/${documentId}`;
}

export function getTicketPath(ticketId) {
  return `${ApiPaths.tickets}/${ticketId}`;
}

export function getQueuePath(traceId) {
  return `${ApiPaths.queue}/${traceId}`;
}

export function getTracePath(traceId) {
  return `${ApiPaths.traces}/${traceId}`;
}
