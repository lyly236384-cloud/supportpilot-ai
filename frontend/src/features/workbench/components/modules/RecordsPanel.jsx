import { useEffect, useState } from "react";
import { DataTable } from "../shared/DataTable";
import { RiskBadge } from "../shared/RiskBadge";
import { StatusChip } from "../shared/StatusChip";
import { TraceDetailPanel } from "../shared/TraceDetailPanel";
import { formatDateTime } from "../shared/formatters";
import {
  DEFAULT_PAGE_SIZE,
  previousPageOffset,
  shouldReloadPreviousPage,
} from "../../utils/paginationHelpers";

const filters = ["全部", "自动解决", "转人工", "建工单"];

export function RecordsPanel({ data }) {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  const selectedRow = rows.find((row) => row.id === selectedId);

  async function loadPage(nextOffset) {
    setLoading(true);
    setError("");
    try {
      const page = await data.fetchTracesPage({
        limit: DEFAULT_PAGE_SIZE,
        offset: nextOffset,
      });
      if (shouldReloadPreviousPage(page)) {
        await loadPage(previousPageOffset(page.offset, DEFAULT_PAGE_SIZE));
        return;
      }
      setRows(page.items);
      setTotal(page.total);
      setOffset(page.offset);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPage(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  useEffect(() => {
    if (!rows.length) {
      setSelectedId("");
      return;
    }
    if (!selectedId || !rows.some((row) => row.id === selectedId)) {
      setSelectedId(rows[0].id);
    }
  }, [rows, selectedId]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      setDetailError("");
      return;
    }

    let cancelled = false;

    async function loadDetail() {
      setDetailLoading(true);
      setDetailError("");
      try {
        const result = await data.fetchTraceDetail(selectedId);
        if (!cancelled) setDetail(result);
      } catch (requestError) {
        if (!cancelled) {
          setDetail(null);
          setDetailError(requestError.message);
        }
      } finally {
        if (!cancelled) setDetailLoading(false);
      }
    }

    loadDetail();
    return () => {
      cancelled = true;
    };
  }, [data, selectedId]);

  return (
    <div className="mt-9 grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section className="rounded-4xl border border-line bg-white p-6 shadow-card">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-[18px] font-semibold leading-[24px] text-ink">AI 工作流记录</h2>
          <div className="flex flex-wrap gap-2">
            {filters.map((filter, index) => (
              <StatusChip key={filter} tone={index === 0 ? "dark" : "neutral"}>
                {filter}
              </StatusChip>
            ))}
          </div>
        </div>

        {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}

        <DataTable
          columns={["记录", "意图", "动作", "知识引用", "风险", "时间"]}
          emptyTitle="暂无处理记录"
          getRowId={(row) => row.id}
          gridTemplate="88px minmax(120px,1fr) 130px minmax(110px,1fr) 72px 76px"
          onRowClick={(row) => setSelectedId(row.id)}
          rows={rows}
          selectedRowId={selectedId}
          renderRow={(row) => [
            row.id,
            row.raw?.intent?.intent ?? row.issueType,
            row.actionLabel,
            row.citations?.[0]?.title ?? row.answer?.slice(0, 12) ?? "知识片段",
            <RiskBadge label={row.riskLabel} risk={row.riskLevel} />,
            formatDateTime(row.createdAt),
          ]}
        />

        <div className="mt-4 flex items-center justify-between text-xs text-muted">
          <span>共 {total} 条</span>
          <button
            className="rounded-full border border-line bg-white px-3 py-1 font-semibold text-slate-600 disabled:opacity-50"
            disabled={loading}
            onClick={() => loadPage(offset + DEFAULT_PAGE_SIZE)}
            type="button"
          >
            下一页
          </button>
        </div>
      </section>

      <TraceDetailPanel detail={detail} loading={detailLoading} error={detailError} />
    </div>
  );
}
