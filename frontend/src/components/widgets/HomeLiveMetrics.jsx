import { useHomeMetrics } from "../../hooks/useHomeMetrics";

export default function HomeLiveMetrics() {
  const {
    statCards,
    activityItems,
    activityEmptyText,
    autoResolutionRate,
    loading,
    error,
    seed,
    seedPending,
    seedError,
    isEmpty,
  } = useHomeMetrics();

  return (
    <section className="border-t border-line bg-white px-5 py-16 sm:px-8">
      <div className="mx-auto max-w-[1232px]">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-brand-600">
              Live Ops
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-ink">实时运营快照</h2>
            <p className="mt-2 text-sm text-muted">
              数据来自 `/api/metrics` 与最近 trace 记录 · AI 自动解决率 {autoResolutionRate}
            </p>
          </div>
          {error ? <p className="text-sm text-red-600">接口异常：{error}</p> : null}
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {statCards.map((card) => (
            <article
              className="rounded-2.5xl border border-line bg-page px-5 py-6 shadow-sm"
              key={card.label}
            >
              <p className="text-sm font-medium text-muted">{card.label}</p>
              {loading ? (
                <div className="skeleton mt-3 h-8 w-20 rounded-lg" />
              ) : (
                <p className="mt-3 text-3xl font-semibold text-ink">{card.value}</p>
              )}
            </article>
          ))}
        </div>

        {isEmpty ? (
          <div className="mt-8 rounded-2.5xl border border-dashed border-brand-300 bg-brand-50/50 p-6 text-center">
            <p className="text-sm font-medium text-brand-700">当前没有运营数据</p>
            <p className="mt-2 text-sm text-brand-600">
              平台将通过 AI 工作流自动运行 8 条客服场景，生成真实的指标、队列和工单数据。
            </p>
            {seedError ? <p className="mt-2 text-sm text-red-600">{seedError}</p> : null}
            <button
              className="mt-4 inline-flex h-10 items-center justify-center rounded-full bg-brand-600 px-6 text-sm font-semibold text-white shadow-button-primary transition-all hover:-translate-y-0.5 hover:shadow-button-primary-hover disabled:opacity-60"
              disabled={seedPending}
              onClick={seed}
              type="button"
            >
              {seedPending ? "生成中…" : "生成演示数据"}
            </button>
          </div>
        ) : null}

        <div className="mt-8 rounded-2.5xl border border-line bg-page p-6">
          <h3 className="text-base font-semibold text-ink">最近服务请求</h3>
          {activityItems.length ? (
            <ul className="mt-4 space-y-3">
              {activityItems.map((item, index) => (
                <li className="rounded-2xl border border-line bg-white px-4 py-3 text-sm text-slate-700" key={`${item}-${index}`}>
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 rounded-2xl border border-dashed border-line bg-white px-4 py-3 text-sm text-muted">
              {loading ? "正在读取最近 trace…" : activityEmptyText}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
