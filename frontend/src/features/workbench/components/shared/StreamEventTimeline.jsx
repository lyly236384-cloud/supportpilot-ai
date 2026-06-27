function formatElapsedMs(ms) {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function describeEvent(event) {
  if (event.type === "step_start") {
    return {
      title: event.display ?? event.step ?? "step_start",
      detail: "节点开始执行",
      tone: "info",
    };
  }

  if (event.type === "step_complete") {
    const output = event.output ?? {};
    return {
      title: event.display ?? event.step ?? "step_complete",
      detail: output.summary ?? "节点执行完成",
      tone: "success",
    };
  }

  if (event.type === "final") {
    const action = event.response?.action ?? "final";
    return {
      title: "工作流完成",
      detail: `动作：${action}`,
      tone: "accent",
    };
  }

  return {
    title: event.type ?? "event",
    detail: "SSE 事件",
    tone: "muted",
  };
}

const toneClasses = {
  info: "border-sky-200 bg-sky-50 text-sky-700",
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  accent: "border-violet-200 bg-violet-50 text-violet-700",
  muted: "border-slate-200 bg-slate-50 text-slate-600",
};

export function StreamEventTimeline({ events = [], pending = false }) {
  if (!events.length && !pending) {
    return <p className="text-sm text-slate-500">运行工作流后，这里会按时间顺序展示 SSE 事件。</p>;
  }

  return (
    <ol className="space-y-3">
      {events.map((event, index) => {
        const meta = describeEvent(event);
        return (
          <li className="flex gap-3" key={`${event.type}-${index}-${event.receivedAt ?? index}`}>
            <div className="flex w-16 shrink-0 flex-col items-end pt-1">
              <span className="text-xs font-medium text-slate-500">
                {formatElapsedMs(event.receivedAt ?? 0)}
              </span>
              <span className="mt-1 text-[10px] uppercase tracking-wide text-slate-400">
                #{index + 1}
              </span>
            </div>
            <div className="relative flex-1 rounded-2xl border bg-white p-4">
              {index < events.length - 1 ? (
                <span className="absolute -bottom-3 left-4 top-full h-3 w-px bg-slate-200" />
              ) : null}
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${toneClasses[meta.tone]}`}
                >
                  {event.type}
                </span>
                <span className="text-sm font-semibold text-ink">{meta.title}</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">{meta.detail}</p>
            </div>
          </li>
        );
      })}

      {pending ? (
        <li className="flex gap-3">
          <div className="w-16 shrink-0 text-right text-xs text-slate-400">…</div>
          <div className="flex-1 rounded-2xl border border-dashed border-slate-200 bg-white p-4 text-sm text-slate-500">
            等待下一个 SSE 事件…
          </div>
        </li>
      ) : null}
    </ol>
  );
}
