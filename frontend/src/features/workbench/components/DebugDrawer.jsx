import { useState } from "react";
import { CitationsView } from "./shared/CitationsView";
import { StatusChip } from "./shared/StatusChip";
import { StreamEventTimeline } from "./shared/StreamEventTimeline";
import { WorkflowStepsView } from "./shared/WorkflowStepsView";
import { ACTION_LABELS } from "../utils/normalizeTrace";

function toPrettyJson(value) {
  return JSON.stringify(value ?? {}, null, 2);
}

export function DebugDrawer({ chat, onRefresh }) {
  const [open, setOpen] = useState(false);
  const [customerId, setCustomerId] = useState("shop_001");
  const [message, setMessage] = useState("我的快递什么时候发货？");

  async function handleRun(event) {
    event.preventDefault();
    await chat.run({ customerId, message });
    await onRefresh?.();
  }

  function loadDemoCase(demoCase) {
    setCustomerId(demoCase.customerId);
    setMessage(demoCase.message);
  }

  return (
    <section className="mt-8 rounded-4xl border border-dashed border-line bg-page/80">
      <button
        className="flex w-full items-center justify-between rounded-4xl px-5 py-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <div>
          <p className="text-sm font-semibold text-slate-700">流程试运行</p>
          <p className="mt-1 text-xs text-slate-500">
            运行客服工作流，查看 SSE 时间线、步骤、引用和原始 JSON；当前示例模板为电商售后 Demo。
          </p>
        </div>
        <span className="text-sm text-slate-500">{open ? "收起" : "展开"}</span>
      </button>

      {open ? (
        <div className="animate-fade-in-up border-t border-dashed border-line px-5 py-5">
          <form className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)_auto]" onSubmit={handleRun}>
            <label className="block text-sm text-slate-600">
              客户 ID
              <input
                className="mt-2 h-10 w-full rounded-2xl border border-line bg-white px-3 text-sm outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                onChange={(event) => setCustomerId(event.target.value)}
                value={customerId}
              />
            </label>
            <label className="block text-sm text-slate-600">
              模拟用户请求
              <textarea
                className="mt-2 min-h-[88px] w-full rounded-2xl border border-line bg-white px-3 py-2 text-sm outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                onChange={(event) => setMessage(event.target.value)}
                value={message}
              />
            </label>
            <div className="flex items-end">
              <button
                className="h-10 rounded-full bg-slate-800 px-5 text-sm font-semibold text-white transition-colors hover:bg-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-60"
                disabled={chat.pending}
                type="submit"
              >
                {chat.pending ? "运行中..." : "运行工作流"}
              </button>
            </div>
          </form>

          <div className="mt-3 flex flex-wrap gap-2">
            {chat.demoCases.map((demoCase) => (
              <button
                className="rounded-full border border-line bg-white px-3 py-1.5 text-xs text-slate-600 transition-colors hover:border-brand-300 hover:text-brand-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-1"
                key={`${demoCase.customerId}-${demoCase.message}`}
                onClick={() => loadDemoCase(demoCase)}
                type="button"
              >
                {demoCase.message}
              </button>
            ))}
          </div>

          {chat.error ? (
            <p className="mt-3 rounded-xl bg-danger-light px-3 py-2 text-sm text-danger">⚠ {chat.error}</p>
          ) : null}

          {chat.result ? (
            <div className="mt-4 rounded-2xl border border-line bg-white p-4">
              <div className="flex flex-wrap items-center gap-2">
                <StatusChip tone="success">{ACTION_LABELS[chat.result.action] ?? chat.result.action}</StatusChip>
                <span className="text-xs text-slate-500">{chat.result.trace_id}</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-700">{chat.result.answer}</p>
            </div>
          ) : null}

          <section className="mt-6">
            <h3 className="text-sm font-semibold text-ink">SSE 事件时间线</h3>
            <div className="mt-3">
              <StreamEventTimeline events={chat.streamEvents} pending={chat.pending} />
            </div>
          </section>

          <div className="mt-6 grid gap-6 xl:grid-cols-2">
            <section>
              <h3 className="text-sm font-semibold text-ink">工作流步骤</h3>
              <div className="mt-3">
                <WorkflowStepsView steps={chat.steps} />
              </div>
            </section>

            <section>
              <h3 className="text-sm font-semibold text-ink">知识库引用</h3>
              <div className="mt-3">
                <CitationsView citations={chat.result?.citations ?? []} />
              </div>
            </section>
          </div>

          <section className="mt-6">
            <h3 className="text-sm font-semibold text-ink">原始数据</h3>
            <pre className="mt-2 max-h-80 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100">
              {toPrettyJson(chat.result ?? chat.streamEvents)}
            </pre>
          </section>
        </div>
      ) : null}
    </section>
  );
}
