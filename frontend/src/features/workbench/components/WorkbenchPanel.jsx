import { WorkbenchBody } from "./WorkbenchBody";
import { moduleKeys, moduleMeta } from "./moduleMeta";

export function WorkbenchPanel({ activeModule, activeMeta, data, onBack, onModuleChange }) {
  const showRebuild = activeModule === "overview";

  return (
    <section className="mx-auto mt-8 max-w-[1232px]">
      {/* Title row: title + back button */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[32px] font-semibold leading-[42px] text-ink">{activeMeta.title}</h1>
          <p className="mt-2 text-sm leading-[22px] text-muted">{activeMeta.desc}</p>
        </div>
        <button
          className="h-10 rounded-full border border-line bg-white px-5 text-sm font-semibold text-slate-600 shadow-sm transition-colors hover:border-brand-200 hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
          onClick={onBack}
          type="button"
        >
          返回工作台
        </button>
      </div>

      {/* Nav row: capsule nav + rebuild button on same line */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
        <div className="inline-flex h-[50px] max-w-full items-center gap-3 overflow-x-auto rounded-full border border-line bg-white p-2 shadow-sm">
          {moduleKeys.map((key) => {
            const isActive = activeModule === key;
            return (
              <button
                className={`h-[34px] min-w-[118px] rounded-full px-5 text-[13px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-1 ${
                  isActive ? "bg-ink text-white" : "text-slate-500 hover:bg-slate-50 hover:text-ink"
                }`}
                key={key}
                onClick={() => onModuleChange(key)}
                type="button"
              >
                {moduleMeta[key].title}
              </button>
            );
          })}
        </div>

        {showRebuild ? (
          <button
            className="h-[42px] rounded-full border border-line bg-white px-4 text-sm font-semibold text-slate-600 shadow-sm transition-all hover:border-brand-200 hover:text-brand-600 hover:shadow-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-60"
            disabled={data.metricsPending}
            onClick={data.rebuildMetrics}
            type="button"
          >
            {data.metricsPending ? "重建中…" : "重建指标"}
          </button>
        ) : null}
      </div>

      <WorkbenchBody activeModule={activeModule} data={data} />
    </section>
  );
}
