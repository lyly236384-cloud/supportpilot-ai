import { useEffect, useState } from "react";
import { DataTable } from "../shared/DataTable";
import { EmptyState } from "../shared/EmptyState";
import { RiskBadge } from "../shared/RiskBadge";
import { StatusChip } from "../shared/StatusChip";
import { formatWaitMinutes } from "../shared/formatters";
import {
  DEFAULT_PAGE_SIZE,
  previousPageOffset,
  shouldReloadPreviousPage,
} from "../../utils/paginationHelpers";

const queueStatuses = [
  { value: "pending", label: "待接管" },
  { value: "in_progress", label: "处理中" },
  { value: "resolved", label: "已处理" },
  { value: "ticket_created", label: "已转工单" },
];

function statusLabel(value) {
  return queueStatuses.find((item) => item.value === value)?.label ?? value;
}

function DetailAction({ active, children }) {
  return (
    <div
      className={`flex h-10 items-center justify-between rounded-2xl border px-4 text-[12px] font-semibold ${
        active
          ? "border-brand-200 bg-brand-50 text-brand-600"
          : "border-line bg-page text-slate-700"
      }`}
    >
      <span>{children}</span>
      <span>+</span>
    </div>
  );
}

export function QueuePanel({ data }) {
  const [rows, setRows] = useState(data.queueRecords);
  const [total, setTotal] = useState(data.queueRecords.length);
  const [offset, setOffset] = useState(0);
  const [selectedId, setSelectedId] = useState(data.queueRecords[0]?.trace_id ?? "");
  const [draft, setDraft] = useState({ status: "pending", assignee: "", note: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectedRow = rows.find((item) => item.trace_id === selectedId);

  useEffect(() => {
    loadPage(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!rows.length) {
      setSelectedId("");
      return;
    }
    if (!selectedId || !rows.some((item) => item.trace_id === selectedId)) {
      setSelectedId(rows[0].trace_id);
    }
  }, [rows, selectedId]);

  useEffect(() => {
    if (!selectedRow) return;
    setDraft({
      status: selectedRow.status,
      assignee: selectedRow.assignee,
      note: selectedRow.note ?? "",
    });
  }, [selectedRow]);

  async function loadPage(nextOffset = 0) {
    setLoading(true);
    setError("");
    try {
      const page = await data.fetchQueueRecordsPage({
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

  async function saveStatus(nextStatus) {
    if (!selectedRow) return;
    await data.updateQueueRecord(selectedRow.trace_id, {
      status: nextStatus,
      assignee: draft.assignee,
      note: draft.note,
    });
    await loadPage(offset);
  }

  async function createTicket() {
    if (!selectedRow) return;
    await data.createTicketFromQueue(selectedRow.trace_id, {
      assignee: draft.assignee,
      priority: "P1",
      note: draft.note,
    });
    await loadPage(offset);
  }

  return (
    <div className="mt-9 grid gap-6 lg:grid-cols-[minmax(0,808px)_minmax(360px,1fr)]">
      <section className="rounded-4xl border border-line bg-white p-6 shadow-card">
        <div className="mb-5 flex items-center justify-between gap-4">
          <h2 className="text-[18px] font-semibold leading-[24px] text-ink">待接管会话</h2>
          <StatusChip tone="warning">高风险优先</StatusChip>
        </div>

        {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}

        <DataTable
          columns={["编号", "问题类型", "风险", "负责人", "等待"]}
          emptyTitle="暂无待接管问题"
          getRowId={(row) => row.trace_id}
          gridTemplate="92px minmax(160px,1fr) 100px 120px 72px"
          onRowClick={(row) => setSelectedId(row.trace_id)}
          rows={rows}
          selectedRowId={selectedId}
          renderRow={(row, index) => [
            row.trace_id,
            row.issue_type,
            <RiskBadge label={row.risk_level === "high" ? "高风险" : statusLabel(row.status)} risk={row.risk_level} />,
            row.assignee || "未分配",
            formatWaitMinutes(row.created_at),
          ]}
        />

        <div className="mt-4 flex items-center justify-between text-xs text-muted">
          <span>共 {total} 条</span>
          <button
            className="rounded-full border border-line bg-white px-3 py-1 font-semibold text-slate-600 transition-colors hover:border-brand-200 hover:text-brand-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-1 disabled:opacity-50"
            disabled={loading}
            onClick={() => loadPage(offset + DEFAULT_PAGE_SIZE)}
            type="button"
          >
            下一页
          </button>
        </div>
      </section>

      <aside className="rounded-4xl border border-line bg-white p-6 shadow-card">
        {selectedRow ? (
          <div className="flex h-full min-h-[460px] flex-col">
            <div className="flex items-start justify-between gap-4">
              <h2 className="text-[18px] font-semibold leading-[24px] text-ink">
                {selectedRow.trace_id} 处理建议
              </h2>
              <RiskBadge risk={selectedRow.risk_level} />
            </div>
            <p className="mt-4 text-[13px] leading-[21px] text-slate-600">
              {selectedRow.risk_reason ||
                "客户问题存在争议或情绪升级。AI 已完成意图识别与知识引用，建议人工接管并保留工单。"}
            </p>

            <div className="mt-8 space-y-4">
              <DetailAction>查看客户画像</DetailAction>
              <DetailAction>引用知识片段</DetailAction>
              <DetailAction active>转为服务工单</DetailAction>
              <label className="block">
                <span className="sr-only">处理备注</span>
                <textarea
                  className="h-24 w-full resize-none rounded-2xl border border-line bg-page px-4 py-3 text-[12px] leading-5 text-slate-700 outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                  onChange={(event) =>
                    setDraft((current) => ({ ...current, note: event.target.value }))
                  }
                  placeholder="记录处理备注"
                  value={draft.note}
                />
              </label>
            </div>

            {data.queueError ? (
              <p className="mt-4 text-sm text-red-600">{data.queueError}</p>
            ) : null}

            <div className="mt-7 flex gap-3 pt-5">
              <button
                className="h-10 flex-1 rounded-full bg-brand-600 px-4 text-sm font-semibold text-white shadow-button-primary transition-all hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-60"
                disabled={data.queuePending}
                onClick={() => saveStatus("in_progress")}
                type="button"
              >
                接管会话
              </button>
              <button
                className="h-10 flex-1 rounded-full border border-line bg-white px-4 text-sm font-semibold text-ink shadow-sm transition-colors hover:border-brand-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-60"
                disabled={data.queuePending}
                onClick={createTicket}
                type="button"
              >
                创建工单
              </button>
            </div>
          </div>
        ) : (
          <EmptyState title="选择一条人工队列记录" desc="支持接管、更新处理状态和转服务工单。" />
        )}
      </aside>
    </div>
  );
}
