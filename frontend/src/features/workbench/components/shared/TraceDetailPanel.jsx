import { useState } from "react";
import { CitationsView } from "./CitationsView";
import { StatusChip } from "./StatusChip";
import { WorkflowStepsView } from "./WorkflowStepsView";
import {
  ACTION_LABELS,
  PRIORITY_LABELS,
  QUEUE_STATUS_LABELS,
  TICKET_STATUS_LABELS,
} from "../../utils/normalizeTrace";

const TABS = [
  { key: "summary", label: "概要" },
  { key: "steps", label: "步骤" },
  { key: "citations", label: "引用" },
  { key: "raw", label: "原始" },
];

function toPrettyJson(value) {
  return JSON.stringify(value ?? {}, null, 2);
}

function MetaRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-2 py-1.5">
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="text-xs font-medium text-slate-700 text-right">{value ?? "-"}</dd>
    </div>
  );
}

export function TraceDetailPanel({ detail, loading, error }) {
  const [activeTab, setActiveTab] = useState("summary");

  // ---- Loading / Error / Empty states (unchanged structure, polished) ----
  if (loading) {
    return (
      <aside className="rounded-4xl border border-line bg-white p-5">
        <h3 className="text-base font-semibold text-ink">记录详情</h3>
        <div className="mt-6 space-y-3">
          <div className="skeleton h-4 w-full rounded" />
          <div className="skeleton h-4 w-3/4 rounded" />
          <div className="skeleton h-20 w-full rounded-2xl" />
        </div>
      </aside>
    );
  }

  if (error) {
    return (
      <aside className="rounded-4xl border border-line bg-white p-5">
        <h3 className="text-base font-semibold text-ink">记录详情</h3>
        <p className="mt-4 text-sm text-danger">{error}</p>
      </aside>
    );
  }

  if (!detail?.trace) {
    return (
      <aside className="rounded-4xl border border-line bg-white p-5">
        <h3 className="text-base font-semibold text-ink">记录详情</h3>
        <p className="mt-4 text-sm text-slate-400">选择左侧一条记录查看完整上下文</p>
      </aside>
    );
  }

  const t = detail.trace;

  // ---- Tab content renderers ----
  const renderSummary = () => (
    <div className="space-y-3">
      <div className="rounded-2xl bg-slate-50 p-3">
        <p className="text-xs font-semibold text-slate-400 mb-1.5">客户消息</p>
        <p className="text-sm text-slate-700">{t.message}</p>
      </div>

      {t.answer ? (
        <div className="rounded-2xl bg-brand-50/50 p-3">
          <p className="text-xs font-semibold text-brand-600/70 mb-1.5">AI 回复</p>
          <p className="text-sm leading-6 text-slate-700">{t.answer}</p>
        </div>
      ) : null}

      {detail.queue ? (
        <div className="rounded-2xl border border-line bg-white p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-slate-500">队列关联</h4>
            <StatusChip tone={detail.queue.status === "resolved" ? "success" : "warning"}>
              {QUEUE_STATUS_LABELS[detail.queue.status] ?? detail.queue.status}
            </StatusChip>
          </div>
          <MetaRow label="负责人" value={detail.queue.assignee} />
          <MetaRow label="关联工单" value={detail.queue.linked_ticket_id} />
          <MetaRow label="备注" value={detail.queue.note} />
        </div>
      ) : null}

      {detail.ticket_record ? (
        <div className="rounded-2xl border border-line bg-white p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-slate-500">工单关联</h4>
            <StatusChip tone={detail.ticket_record.status === "Closed" || detail.ticket_record.status === "Resolved" ? "success" : "warning"}>
              {TICKET_STATUS_LABELS[detail.ticket_record.status] ?? detail.ticket_record.status}
            </StatusChip>
          </div>
          <MetaRow label="工单号" value={detail.ticket_record.ticket_id} />
          <MetaRow label="负责人" value={detail.ticket_record.assignee} />
          <MetaRow label="优先级" value={PRIORITY_LABELS[detail.ticket_record.priority] ?? detail.ticket_record.priority} />
        </div>
      ) : null}

      <dl className="rounded-2xl border border-line bg-white p-3 space-y-0 divide-y divide-slate-50">
        <MetaRow label="Trace ID" value={t.trace_id} />
        <MetaRow label="意图" value={t.intent?.intent} />
        <MetaRow label="置信度" value={t.intent?.confidence != null ? `${(t.intent.confidence * 100).toFixed(0)}%` : "-"} />
        <MetaRow label="风险等级" value={t.risk?.risk_level} />
        <MetaRow label="耗时" value={t.elapsed_ms != null ? `${t.elapsed_ms}ms` : "-"} />
      </dl>
    </div>
  );

  const renderSteps = () => (
    t.workflow_steps?.length ? (
      <WorkflowStepsView steps={t.workflow_steps} compact />
    ) : (
      <p className="text-sm text-slate-400 py-4 text-center">暂无工作流步骤</p>
    )
  );

  const renderCitations = () => (
    t.citations?.length ? (
      <CitationsView citations={t.citations} />
    ) : (
      <p className="text-sm text-slate-400 py-4 text-center">暂无知识引用</p>
    )
  );

  const renderRaw = () => (
    <pre className="max-h-[50vh] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">
      {toPrettyJson(detail)}
    </pre>
  );

  const tabContent = {
    summary: renderSummary,
    steps: renderSteps,
    citations: renderCitations,
    raw: renderRaw,
  };

  return (
    <aside className="rounded-4xl border border-line bg-white shadow-sm flex flex-col overflow-hidden sticky top-6 max-h-[calc(100vh-7rem)]">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between px-5 pt-5 pb-1">
        <h3 className="text-base font-semibold text-ink">记录详情</h3>
        <StatusChip tone={t.action === "auto_reply" ? "success" : t.action === "handoff" ? "warning" : "dark"}>
          {ACTION_LABELS[t.action] ?? t.action ?? "trace"}
        </StatusChip>
      </div>

      {/* Tabs */}
      <nav className="shrink-0 flex gap-1 px-5 pt-2 pb-3 border-b border-slate-50">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key;
          const hasContent =
            tab.key === "steps" ? !!t.workflow_steps?.length
            : tab.key === "citations" ? !!t.citations?.length
            : true;
          return (
            <button
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                isActive
                  ? "bg-ink text-white"
                  : hasContent
                  ? "text-slate-500 hover:text-ink hover:bg-slate-100"
                  : "text-slate-300"
              }`}
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              type="button"
            >
              {tab.label}
              {tab.key === "steps" && t.workflow_steps?.length ? ` ${t.workflow_steps.length}` : ""}
              {tab.key === "citations" && t.citations?.length ? ` ${t.citations.length}` : ""}
            </button>
          );
        })}
      </nav>

      {/* Tab Content — scrollable */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {(tabContent[activeTab] ?? tabContent.summary)()}
      </div>
    </aside>
  );
}
