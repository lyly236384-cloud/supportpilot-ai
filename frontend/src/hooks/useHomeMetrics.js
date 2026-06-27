import { useCallback, useEffect, useState } from "react";
import { fetchMetrics, fetchTracesPage, seedDemoData } from "../services/supportApi";
import { formatNumber, formatRate } from "../features/workbench/components/shared/formatters";

function buildStatCards(metrics, loading) {
  const cards = [
    ["咨询总量", metrics?.total_conversations],
    ["AI 自动处理", metrics?.auto_reply_count],
    ["转人工", metrics?.handoff_count],
    ["服务工单", metrics?.ticket_count],
  ];

  return cards.map(([label, value]) => ({
    label,
    value: loading ? "—" : formatNumber(value),
  }));
}

export function useHomeMetrics() {
  const [metrics, setMetrics] = useState(null);
  const [recentMessages, setRecentMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [seedPending, setSeedPending] = useState(false);
  const [seedError, setSeedError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [metricsData, recentPage] = await Promise.all([
        fetchMetrics(),
        fetchTracesPage({ limit: 3, offset: 0 }),
      ]);
      setMetrics(metricsData);
      setRecentMessages(
        recentPage.items
          .map((trace) => trace.message)
          .filter(Boolean)
          .slice(0, 3),
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const seed = useCallback(async () => {
    setSeedPending(true);
    setSeedError("");
    try {
      await seedDemoData(false);
      await refresh();
    } catch (requestError) {
      setSeedError(requestError.message);
    } finally {
      setSeedPending(false);
    }
  }, [refresh]);

  const statCards = buildStatCards(metrics, loading);
  const activityItems = recentMessages;
  const activityEmptyText = seedPending
    ? "正在通过 AI 工作流生成演示数据，预计需要数十秒…"
    : "暂无处理记录。请在工作台运行一条服务流程，或点击下方「生成演示数据」自动填充。";
  const autoResolutionRate = loading ? "—" : formatRate(metrics?.auto_resolution_rate);
  const isEmpty = !loading && (metrics?.total_conversations ?? 0) === 0;

  return {
    metrics,
    statCards,
    activityItems,
    activityEmptyText,
    autoResolutionRate,
    loading,
    error,
    refresh,
    seed,
    seedPending,
    seedError,
    isEmpty,
  };
}
