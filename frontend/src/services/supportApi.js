import { requestFormData, requestJson } from "./apiClient";
import { ApiPaths, getKnowledgeDocumentPath, getQueuePath, getTicketPath, getTracePath } from "../types/apiContracts";

function buildQueryString(params = {}) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchPaginated(path, params = {}) {
  return requestJson(`${path}${buildQueryString({ ...params, envelope: true })}`);
}

export function sendChatMessage(payload) {
  return requestJson(ApiPaths.chat, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function sendProductChatMessage(payload) {
  return requestJson(ApiPaths.productChat, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchMetrics() {
  return requestJson(ApiPaths.metrics);
}

export function rebuildMetrics() {
  return requestJson(ApiPaths.metricsRebuild, {
    method: "POST",
  });
}

export function fetchMetricsTrends({ hours = 24 } = {}) {
  return requestJson(`${ApiPaths.metricsTrends}?hours=${hours}`);
}

export function fetchTraces(limit = 50) {
  return requestJson(`${ApiPaths.traces}?limit=${limit}`);
}

export function fetchTracesPage({ limit = 15, offset = 0 } = {}) {
  return fetchPaginated(ApiPaths.traces, { limit, offset });
}

export function downloadTracesExport({ all = true, limit } = {}) {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
  const params = new URLSearchParams();
  if (all) {
    params.set("all", "true");
  } else if (limit !== undefined) {
    params.set("limit", String(limit));
  }
  const query = params.toString();
  const url = `${API_BASE_URL}${ApiPaths.tracesExport}${query ? `?${query}` : ""}`;
  const link = document.createElement("a");
  link.href = url;
  link.download = "supportpilot_traces.csv";
  link.rel = "noopener";
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export function fetchTraceDetail(traceId) {
  return requestJson(getTracePath(traceId));
}

export function fetchKnowledgeDocuments() {
  return requestJson(ApiPaths.knowledgeDocuments);
}

export function fetchKnowledgeDocument(documentId) {
  return requestJson(getKnowledgeDocumentPath(documentId));
}

export function createKnowledgeDocument(payload) {
  return requestJson(ApiPaths.knowledgeDocuments, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateKnowledgeDocument(documentId, payload) {
  return requestJson(getKnowledgeDocumentPath(documentId), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteKnowledgeDocument(documentId) {
  return requestJson(getKnowledgeDocumentPath(documentId), {
    method: "DELETE",
  });
}

export function importKnowledgeDocument({ file, title, category, status = "enabled" }) {
  const formData = new FormData();
  formData.set("file", file);
  if (title) formData.set("title", title);
  if (category) formData.set("category", category);
  formData.set("status", status);
  return requestFormData(ApiPaths.knowledgeImport, formData);
}

export function seedDemoData(force = false) {
  return requestJson(`${ApiPaths.seed}?force=${force}`, { method: "POST" });
}

export function fetchCustomers() {
  return requestJson(ApiPaths.customers);
}

export function reindexKnowledgeBase() {
  return requestJson(ApiPaths.knowledgeReindex, {
    method: "POST",
  });
}

export function fetchTickets(filters = {}) {
  return requestJson(`${ApiPaths.tickets}${buildQueryString(filters)}`);
}

export function fetchTicketsPage({ limit = 15, offset = 0, ...filters } = {}) {
  return fetchPaginated(ApiPaths.tickets, { limit, offset, ...filters });
}

export function updateTicket(ticketId, payload) {
  return requestJson(getTicketPath(ticketId), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function fetchQueueRecords(filters = {}) {
  return requestJson(`${ApiPaths.queue}${buildQueryString(filters)}`);
}

export function fetchQueueRecordsPage({ limit = 15, offset = 0, ...filters } = {}) {
  return fetchPaginated(ApiPaths.queue, { limit, offset, ...filters });
}

export function updateQueueRecord(traceId, payload) {
  return requestJson(getQueuePath(traceId), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createTicketFromQueue(traceId, payload) {
  return requestJson(`${getQueuePath(traceId)}/ticket`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
