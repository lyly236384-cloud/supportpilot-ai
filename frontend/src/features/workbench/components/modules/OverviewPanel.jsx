import { useEffect, useState } from "react";
import { fetchMetricsTrends } from "../../../../services/supportApi";
import { RiskBadge } from "../shared/RiskBadge";
import { StatusChip } from "../shared/StatusChip";
import { EmptyState } from "../shared/EmptyState";
import { displayMetric, formatDateTime, formatDurationMs, formatNumber, formatRate } from "../shared/formatters";

const metricStyles = {
  blue: { icon: "from-blue-100 to-blue-300 text-brand-600", spark: "bg-brand-600", chip: "neutral" },
  cyan: { icon: "from-cyan-100 to-cyan-300 text-cyan-600", spark: "bg-cyan-500", chip: "neutral" },
  orange: { icon: "from-orange-100 to-orange-300 text-orange-600", spark: "bg-orange-500", chip: "neutral" },
  emerald: { icon: "from-emerald-100 to-emerald-300 text-emerald-600", spark: "bg-emerald-500", chip: "neutral" },
};

function MetricCard({ label, value, color }) {
  const style = metricStyles[color];

  return (
    <article className="rounded-4xl border border-line bg-white p-6 shadow-card">
      <div className="flex items-center gap-4">
        <div
          className={`flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br text-xs font-bold ${style.icon}`}
        >
          {label.slice(0, 1)}
        </div>
        <p className="text-[13px] font-medium text-muted">{label}</p>
      </div>
      <div className="mt-7 flex items-end justify-between gap-4">
        <p className="text-[32px] font-semibold leading-[38px] text-ink">{value}</p>
      </div>
    </article>
  );
}

function TrendPanel({ metrics }) {
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadTrends() {
      setLoading(true);
      setError("");
      try {
        const payload = await fetchMetricsTrends({ hours: 12 });
        if (!cancelled) setTrends(payload);
      } catch (requestError) {
        if (!cancelled) setError(requestError.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadTrends();
    return () => {
      cancelled = true;
    };
  }, []);

  const points = trends?.points ?? [];
  const numericPoints = points.map((point) => Number(point.auto_resolution_rate) || 0);
  const maxRate = Math.max(...numericPoints, 0.01);

  return (
    <section className="rounded-4xl border border-line bg-white p-7 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-[18px] font-semibold leading-[24px] text-ink">AI 解决率趋势</h2>
          <p className="mt-2 text-[13px] leading-5 text-muted">
            按小时聚合，数据来自 `/api/metrics/trends`（近 12 小时）。
          </p>
        </div>
        <StatusChip tone="success">解决率 {formatRate(metrics?.auto_resolution_rate)}</StatusChip>
      </div>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      {loading ? (
        <div className="mt-6 flex h-[132px] items-end gap-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <div className="skeleton flex-1 rounded-[5px]" key={i} style={{ height: 24 + ((i * 13) % 80) }} />
          ))}
        </div>
      ) : null}
      {!loading && !points.some((point) => point.total > 0) ? (
        <div className="mt-6 flex h-[132px] items-center justify-center rounded-2xl border border-dashed border-line bg-page px-6 text-center text-sm text-muted">
          暂无处理记录数据。运行流程试运行后趋势会自动出现。
        </div>
      ) : null}
      {!loading && points.some((point) => point.total > 0) ? (
        <div className="mt-6 flex h-[132px] items-end gap-1 sm:gap-2">
          {points.map((point) => {
            const rate = Number(point.auto_resolution_rate) || 0;
            const height = Math.max(8, Math.round((rate / maxRate) * 94));
            return (
              <div className="flex flex-1 flex-col items-center gap-2" key={point.bucket} title={`${point.bucket} · ${point.total} 条`}>
                <span
                  className="w-full max-w-[47px] rounded-[5px] bg-brand-600"
                  style={{ height, opacity: 0.45 + (rate / maxRate) * 0.55 }}
                />
                <span className="hidden text-[10px] text-muted sm:block">
                  {new Date(point.bucket).getHours().toString().padStart(2, "0")}:00
                </span>
              </div>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}

function InsightPanel({ metrics }) {
  const items = [
    ["AI 自动解决率", formatRate(metrics?.auto_resolution_rate)],
    ["平均响应", formatDurationMs(metrics?.avg_elapsed_ms)],
    ["高风险记录", formatNumber(metrics?.high_risk_count)],
    ["Token 估算", formatNumber(metrics?.total_estimated_tokens)],
  ];

  return (
    <aside className="rounded-4xl border border-line bg-gradient-to-r from-white to-blue-50 p-7 shadow-card">
      <div>
        <h2 className="text-[18px] font-semibold leading-[24px] text-ink">运营洞察</h2>
        <p className="mt-3 max-w-[320px] text-[13px] leading-[21px] text-muted">
          以下数值来自后端 metrics 聚合。
        </p>
      </div>
      <div className="mt-7 space-y-3">
        {items.map(([label, value]) => (
          <div
            className="flex h-10 items-center justify-between rounded-full border border-line bg-white px-4"
            key={label}
          >
            <span className="text-[13px] font-medium text-muted">{label}</span>
            <span className="text-[15px] font-semibold text-ink">{value}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}

function RecentActivity({ data }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadRecent() {
      setLoading(true);
      setError("");
      try {
        const page = await data.fetchTracesPage({ limit: 5, offset: 0 });
        if (!cancelled) setRows(page.items);
      } catch (requestError) {
        if (!cancelled) setError(requestError.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadRecent();
    return () => {
      cancelled = true;
    };
  }, [data]);

  return (
    <section className="rounded-4xl border border-line bg-white p-7 shadow-card">
      <h2 className="text-lg font-semibold leading-6 text-ink">最近活动</h2>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      {loading ? (
        <div className="mt-4 space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div className="skeleton h-12 rounded-2xl" key={i} />
          ))}
        </div>
      ) : null}
      {!loading && !rows.length ? (
        <EmptyState
          className="mt-4"
          desc="在工作台流程试运行中运行一条服务工作流后，这里会显示真实处理记录。"
          title="暂无处理记录"
        />
      ) : null}
      {!loading && rows.length ? (
        <>
          <div className="mt-5 grid grid-cols-[120px_minmax(0,1.2fr)_minmax(0,1fr)_120px_100px] gap-3 px-4 text-xs font-semibold text-muted max-lg:hidden">
            <span>记录</span>
            <span>客户问题</span>
            <span>动作</span>
            <span>风险</span>
            <span>时间</span>
          </div>
          <div className="mt-3 space-y-3">
            {rows.map((row) => (
              <div
                className="grid min-h-12 grid-cols-1 gap-1 rounded-2xl border border-line bg-page px-4 py-3 text-sm text-slate-700 lg:grid-cols-[120px_minmax(0,1.2fr)_minmax(0,1fr)_120px_100px] lg:items-center lg:gap-3"
                key={row.id}
              >
                <span className="text-xs text-muted lg:text-sm lg:text-slate-700">{row.id}</span>
                <span className="truncate font-medium lg:font-normal">{row.message}</span>
                <span className="text-muted lg:text-slate-700">{row.actionLabel}</span>
                <RiskBadge label={row.riskLabel} risk={row.riskLevel} />
                <span className="text-xs text-muted lg:text-sm lg:text-slate-700">{formatDateTime(row.createdAt)}</span>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

export function OverviewPanel({ data }) {
  const metrics = data.metrics ?? {};
  const loading = data.loading;
  const cards = [
    ["咨询总量", displayMetric(metrics.total_conversations, loading), "blue"],
    ["AI 自动处理", displayMetric(metrics.auto_reply_count, loading), "cyan"],
    ["转人工", displayMetric(metrics.handoff_count, loading), "orange"],
    ["服务工单", displayMetric(metrics.ticket_count, loading), "emerald"],
  ];

  return (
    <div className="mt-6 space-y-6">
      {data.metricsError ? <p className="text-sm text-red-600">{data.metricsError}</p> : null}
      {data.error ? <p className="text-sm text-red-600">数据加载失败：{data.error}</p> : null}

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {cards.map(([label, value, color]) => (
          <MetricCard color={color} key={label} label={label} value={value} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(320px,0.9fr)]">
        <TrendPanel metrics={metrics} />
        <InsightPanel metrics={metrics} />
      </div>

      <div>
        <RecentActivity data={data} />
      </div>
    </div>
  );
}
