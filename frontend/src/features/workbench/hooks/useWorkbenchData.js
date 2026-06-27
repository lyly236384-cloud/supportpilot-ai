import { useCallback, useEffect, useState } from "react";
import {
  createKnowledgeDocument,
  createTicketFromQueue,
  deleteKnowledgeDocument,
  fetchKnowledgeDocument,
  fetchKnowledgeDocuments,
  fetchMetrics,
  rebuildMetrics,
  fetchQueueRecords as apiFetchQueueRecords,
  fetchQueueRecordsPage as apiFetchQueueRecordsPage,
  fetchTickets as apiFetchTickets,
  fetchTicketsPage as apiFetchTicketsPage,
  fetchTraceDetail,
  fetchTracesPage as apiFetchTracesPage,
  importKnowledgeDocument,
  reindexKnowledgeBase,
  updateQueueRecord,
  updateTicket,
  updateKnowledgeDocument,
} from "../../../services/supportApi";
import { normalizeTrace } from "../utils/normalizeTrace";

const initialState = {
  metrics: null,
  queueRecords: [],
  tickets: [],
  knowledgeDocuments: [],
};

export function useWorkbenchData() {
  const [data, setData] = useState(initialState);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [knowledgePending, setKnowledgePending] = useState(false);
  const [knowledgeError, setKnowledgeError] = useState("");
  const [queuePending, setQueuePending] = useState(false);
  const [queueError, setQueueError] = useState("");
  const [ticketPending, setTicketPending] = useState(false);
  const [ticketError, setTicketError] = useState("");
  const [metricsPending, setMetricsPending] = useState(false);
  const [metricsError, setMetricsError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [queueRecords, tickets, metrics, knowledgeDocuments] = await Promise.all([
        apiFetchQueueRecords(),
        apiFetchTickets(),
        fetchMetrics(),
        fetchKnowledgeDocuments(),
      ]);

      setData({
        queueRecords,
        tickets,
        metrics,
        knowledgeDocuments,
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const runKnowledgeMutation = useCallback(
    async (operation) => {
      setKnowledgePending(true);
      setKnowledgeError("");

      try {
        const result = await operation();
        await refresh();
        return result;
      } catch (requestError) {
        setKnowledgeError(requestError.message);
        throw requestError;
      } finally {
        setKnowledgePending(false);
      }
    },
    [refresh],
  );

  const runTicketMutation = useCallback(
    async (operation) => {
      setTicketPending(true);
      setTicketError("");

      try {
        const result = await operation();
        await refresh();
        return result;
      } catch (requestError) {
        setTicketError(requestError.message);
        throw requestError;
      } finally {
        setTicketPending(false);
      }
    },
    [refresh],
  );

  const runQueueMutation = useCallback(
    async (operation) => {
      setQueuePending(true);
      setQueueError("");

      try {
        const result = await operation();
        await refresh();
        return result;
      } catch (requestError) {
        setQueueError(requestError.message);
        throw requestError;
      } finally {
        setQueuePending(false);
      }
    },
    [refresh],
  );

  const runMetricsMutation = useCallback(
    async (operation) => {
      setMetricsPending(true);
      setMetricsError("");

      try {
        const result = await operation();
        await refresh();
        return result;
      } catch (requestError) {
        setMetricsError(requestError.message);
        throw requestError;
      } finally {
        setMetricsPending(false);
      }
    },
    [refresh],
  );

  return {
    ...data,
    loading,
    error,
    refresh,
    knowledgePending,
    knowledgeError,
    fetchKnowledgeDocument,
    createKnowledgeDocument: (payload) =>
      runKnowledgeMutation(() => createKnowledgeDocument(payload)),
    updateKnowledgeDocument: (documentId, payload) =>
      runKnowledgeMutation(() => updateKnowledgeDocument(documentId, payload)),
    deleteKnowledgeDocument: (documentId) =>
      runKnowledgeMutation(() => deleteKnowledgeDocument(documentId)),
    importKnowledgeDocument: (payload) =>
      runKnowledgeMutation(() => importKnowledgeDocument(payload)),
    reindexKnowledgeBase: () => runKnowledgeMutation(() => reindexKnowledgeBase()),
    queuePending,
    queueError,
    fetchQueueRecords: (filters) => apiFetchQueueRecords(filters),
    fetchQueueRecordsPage: (params) => apiFetchQueueRecordsPage(params),
    updateQueueRecord: (traceId, payload) =>
      runQueueMutation(() => updateQueueRecord(traceId, payload)),
    createTicketFromQueue: (traceId, payload) =>
      runQueueMutation(() => createTicketFromQueue(traceId, payload)),
    ticketPending,
    ticketError,
    fetchTickets: (filters) => apiFetchTickets(filters),
    fetchTicketsPage: (params) => apiFetchTicketsPage(params),
    fetchTracesPage: async (params) => {
      const page = await apiFetchTracesPage(params);
      return {
        ...page,
        items: page.items.map(normalizeTrace),
      };
    },
    fetchTraceDetail,
    updateTicket: (ticketId, payload) => runTicketMutation(() => updateTicket(ticketId, payload)),
    metricsPending,
    metricsError,
    rebuildMetrics: () => runMetricsMutation(() => rebuildMetrics()),
  };
}
