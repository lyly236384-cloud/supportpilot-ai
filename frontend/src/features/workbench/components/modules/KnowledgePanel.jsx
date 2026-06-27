import { useEffect, useState } from "react";
import { DataTable } from "../shared/DataTable";
import { EmptyState } from "../shared/EmptyState";
import { StatusChip } from "../shared/StatusChip";
import { formatDate, formatDateTime, formatNumber } from "../shared/formatters";

const emptyForm = {
  title: "",
  category: "",
  content: "",
  status: "enabled",
};

function statusText(status) {
  return status === "enabled" ? "启用" : "停用";
}

function formatUsageCount(value) {
  return formatNumber(value ?? 0);
}

function EditorActions({
  disabled,
  mode,
  onCreate,
  onDelete,
  onEdit,
  onStatusChange,
  onView,
}) {
  const actions = [
    ["查看", onView, false],
    ["编辑", onEdit, true],
    ["启用", () => onStatusChange("enabled"), false],
    ["停用", () => onStatusChange("disabled"), false],
    ["删除", onDelete, false],
  ];

  return (
    <div className="mt-6 grid grid-cols-2 gap-3">
      {actions.map(([label, handler, primary]) => (
        <button
          className={`h-10 rounded-full border px-4 text-sm font-semibold disabled:opacity-50 ${
            primary || mode === "edit"
              ? "border-brand-600 bg-brand-600 text-white"
              : "border-line bg-white text-ink"
          } ${label === "删除" ? "col-span-1" : ""}`}
          disabled={disabled}
          key={label}
          onClick={handler}
          type="button"
        >
          {label}
        </button>
      ))}
      <button
        className="h-10 rounded-full border border-line bg-white px-4 text-sm font-semibold text-ink"
        onClick={onCreate}
        type="button"
      >
        新增
      </button>
    </div>
  );
}

export function KnowledgePanel({ data }) {
  const documents = data.knowledgeDocuments;
  const [selectedId, setSelectedId] = useState(documents[0]?.id ?? "");
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [mode, setMode] = useState("view");
  const [form, setForm] = useState(emptyForm);
  const [panelError, setPanelError] = useState("");
  const [reindexMessage, setReindexMessage] = useState("");
  const [importMessage, setImportMessage] = useState("");
  const [lastReindex, setLastReindex] = useState(null);

  useEffect(() => {
    if (!documents.length) {
      setSelectedId("");
      setSelectedDocument(null);
      return;
    }

    if (!selectedId || !documents.some((item) => item.id === selectedId)) {
      setSelectedId(documents[0].id);
    }
  }, [documents, selectedId]);

  useEffect(() => {
    async function loadDetail() {
      if (!selectedId || mode === "create") return;

      try {
        setPanelError("");
        const detail = await data.fetchKnowledgeDocument(selectedId);
        setSelectedDocument(detail);

        if (mode === "edit") {
          setForm({
            title: detail.title,
            category: detail.category,
            content: detail.content,
            status: detail.status,
          });
        }
      } catch (requestError) {
        setPanelError(requestError.message);
      }
    }

    loadDetail();
  }, [data, mode, selectedId]);

  const hasSelection = Boolean(selectedId);

  function startCreate() {
    setMode("create");
    setPanelError("");
    setSelectedDocument(null);
    setForm(emptyForm);
  }

  function startEdit() {
    if (!selectedDocument) return;
    setMode("edit");
    setPanelError("");
    setForm({
      title: selectedDocument.title,
      category: selectedDocument.category,
      content: selectedDocument.content,
      status: selectedDocument.status,
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setPanelError("");

    try {
      if (mode === "create") {
        const created = await data.createKnowledgeDocument(form);
        setSelectedId(created.id);
      } else if (selectedId) {
        await data.updateKnowledgeDocument(selectedId, form);
      }
      setMode("view");
    } catch (requestError) {
      setPanelError(requestError.message);
    }
  }

  async function handleDelete() {
    if (!selectedId) return;

    try {
      setPanelError("");
      await data.deleteKnowledgeDocument(selectedId);
      setSelectedId("");
      setSelectedDocument(null);
      setMode("view");
    } catch (requestError) {
      setPanelError(requestError.message);
    }
  }

  async function handleStatusChange(status) {
    if (!selectedId) return;

    try {
      setPanelError("");
      await data.updateKnowledgeDocument(selectedId, { status });
      setMode("view");
    } catch (requestError) {
      setPanelError(requestError.message);
    }
  }

  async function handleImport(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    try {
      setPanelError("");
      setImportMessage("");
      const imported = await data.importKnowledgeDocument({ file });
      setSelectedId(imported.id);
      setMode("view");
      setImportMessage(`已导入 Markdown 文档：${imported.title}。建议重建索引后用于检索。`);
    } catch (requestError) {
      setPanelError(requestError.message);
    }
  }

  async function handleReindex() {
    try {
      setPanelError("");
      setReindexMessage("");
      const result = await data.reindexKnowledgeBase();
      setLastReindex(result);
      setReindexMessage(
        `索引已重建：${result.document_count} 篇文档，${result.chunk_count} 个片段。`,
      );
    } catch (requestError) {
      setPanelError(requestError.message);
    }
  }

  const statDocument = selectedDocument ?? documents.find((item) => item.id === selectedId);
  const enabledCount = documents.filter((item) => item.status === "enabled").length;
  const disabledCount = documents.length - enabledCount;

  return (
    <div className="mt-9 grid gap-6 lg:grid-cols-[minmax(0,808px)_minmax(360px,1fr)]">
      <section className="rounded-4xl border border-line bg-white p-6 shadow-card">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-[18px] font-semibold leading-[24px] text-ink">知识文档</h2>
          <div className="flex gap-2">
            <button
              className="h-9 rounded-full bg-brand-600 px-5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
              onClick={startCreate}
              type="button"
            >
              新增
            </button>
            <label className="inline-flex h-9 cursor-pointer items-center rounded-full border border-line bg-white px-5 text-sm font-semibold text-ink transition-colors hover:border-brand-200 focus-within:ring-2 focus-within:ring-brand-600 focus-within:ring-offset-2">
              导入 Markdown
              <input accept=".md,.markdown,text/markdown" className="hidden" onChange={handleImport} type="file" />
            </label>
            <button
              className="h-9 rounded-full border border-line bg-white px-5 text-sm font-semibold text-ink transition-colors hover:border-brand-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-50"
              disabled={data.knowledgePending}
              onClick={handleReindex}
              type="button"
            >
              重建索引
            </button>
          </div>
        </div>

        {importMessage ? (
          <p className="mb-2 text-[13px] leading-6 text-blue-700">{importMessage}</p>
        ) : null}

        {reindexMessage ? (
          <p className="mb-2 text-[13px] leading-6 text-emerald-700">{reindexMessage}</p>
        ) : null}

        <DataTable
          columns={["文档", "分类", "状态", "引用", "更新"]}
          emptyTitle="暂无知识文档"
          getRowId={(document) => document.id}
          gridTemplate="minmax(180px,1fr) 110px 90px 80px 90px"
          onRowClick={(row) => {
            setSelectedId(row.id);
            setMode("view");
          }}
          rows={documents}
          selectedRowId={selectedId}
          renderRow={(document) => [
            document.title,
            document.category,
            <StatusChip tone={document.status === "enabled" ? "success" : "neutral"}>
              {statusText(document.status)}
            </StatusChip>,
            formatNumber(document.usage_count ?? 0),
            formatDate(document.updated_at),
          ]}
        />
      </section>

      <aside className="rounded-4xl border border-line bg-white p-6 shadow-card">
        {data.knowledgeError || panelError ? (
          <p className="mb-4 text-sm leading-6 text-red-600">{data.knowledgeError || panelError}</p>
        ) : null}

        {mode === "view" ? (
          statDocument ? (
            <>
              <div className="flex items-start justify-between gap-4">
                <h2 className="text-[18px] font-semibold leading-[24px] text-ink">
                  {statDocument.title}
                </h2>
                <StatusChip tone={statDocument.status === "enabled" ? "success" : "neutral"}>
                  {statDocument.status === "enabled" ? "已启用" : "已停用"}
                </StatusChip>
              </div>
              <p className="mt-4 text-[13px] leading-[21px] text-slate-600">
                {selectedDocument?.content?.slice(0, 110) ||
                  "用于回答服务政策、处理流程、升级规则等标准问题。AI 可引用该文档中的规则片段并返回来源。"}
              </p>
              <div className="mt-6 grid grid-cols-3 gap-3">
                {[
                  ["引用次数", formatUsageCount(statDocument.usage_count)],
                  ["启用文档", formatNumber(enabledCount)],
                  ["停用文档", formatNumber(disabledCount)],
                ].map(([label, value]) => (
                  <div
                    className="rounded-2.5xl border border-line bg-page p-4"
                    key={label}
                  >
                    <p className="text-xl font-semibold leading-6 text-ink">{value}</p>
                    <p className="mt-1 text-xs leading-4 text-muted">{label}</p>
                  </div>
                ))}
              </div>

              <EditorActions
                disabled={!hasSelection || data.knowledgePending}
                mode={mode}
                onCreate={startCreate}
                onDelete={handleDelete}
                onEdit={startEdit}
                onStatusChange={handleStatusChange}
                onView={() => setMode("view")}
              />

              <div className="mt-6 rounded-2.5xl border border-brand-200 bg-gradient-to-r from-blue-50 to-white p-5">
                <h3 className="text-[15px] font-semibold leading-[20px] text-ink">
                  {lastReindex ? "索引已就绪" : "索引状态"}
                </h3>
                <p className="mt-1.5 text-[12px] leading-5 text-muted">
                  {lastReindex
                    ? `最近重建：${formatDateTime(lastReindex.indexed_at)} · ${lastReindex.document_count} 篇文档 · ${lastReindex.chunk_count} 个片段 · 检索器 ${lastReindex.retriever}`
                    : `当前库内 ${formatNumber(documents.length)} 篇文档（启用 ${formatNumber(enabledCount)} / 停用 ${formatNumber(disabledCount)}）。点击「重建索引」后此处显示最近一次结果。`}
                </p>
              </div>
            </>
          ) : (
            <EmptyState title="选择一篇文档查看详情" desc="支持查看正文、切换状态和继续编辑。" />
          )
        ) : (
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-[18px] font-semibold leading-[24px] text-ink">
                {mode === "create" ? "新增文档" : "编辑文档"}
              </h2>
              <StatusChip tone="info">{mode === "create" ? "新建" : "编辑中"}</StatusChip>
            </div>
            <label className="block">
              <span className="text-sm font-semibold text-slate-700">文档名称</span>
              <input
                className="mt-2 h-11 w-full rounded-2xl border border-line bg-white px-4 text-sm outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
                required
                value={form.title}
              />
            </label>
            <label className="block">
              <span className="text-sm font-semibold text-slate-700">分类</span>
              <input
                className="mt-2 h-11 w-full rounded-2xl border border-line bg-white px-4 text-sm outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                onChange={(event) =>
                  setForm((current) => ({ ...current, category: event.target.value }))
                }
                required
                value={form.category}
              />
            </label>
            <label className="block">
              <span className="text-sm font-semibold text-slate-700">状态</span>
              <select
                className="mt-2 h-11 w-full rounded-2xl border border-line bg-white px-4 text-sm outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
                value={form.status}
              >
                <option value="enabled">启用</option>
                <option value="disabled">停用</option>
              </select>
            </label>
            <label className="block">
              <span className="text-sm font-semibold text-slate-700">正文</span>
              <textarea
                className="mt-2 min-h-40 w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm leading-6 outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                onChange={(event) => setForm((current) => ({ ...current, content: event.target.value }))}
                required
                value={form.content}
              />
            </label>
            <div className="flex gap-3">
              <button
                className="h-10 rounded-full bg-brand-600 px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-50"
                disabled={data.knowledgePending}
                type="submit"
              >
                {mode === "create" ? "创建文档" : "保存修改"}
              </button>
              <button
                className="h-10 rounded-full border border-line bg-white px-4 text-sm font-semibold text-slate-700 transition-colors hover:border-brand-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
                onClick={() => setMode("view")}
                type="button"
              >
                取消
              </button>
            </div>
          </form>
        )}
      </aside>
    </div>
  );
}
