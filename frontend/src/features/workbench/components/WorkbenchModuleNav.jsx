import { workbenchModules } from "../data/modules";
import { moduleKeys, moduleMeta } from "./moduleMeta";

export function WorkbenchModuleNav({ onModuleChange }) {
  return (
    <section className="mx-auto grid max-w-[1232px] grid-cols-1 gap-6 px-0 sm:grid-cols-2 lg:grid-cols-3">
      {workbenchModules.map((module, index) => {
        const key = moduleKeys[index];
        const meta = moduleMeta[key];

        return (
          <button
            className="group flex min-h-[154px] items-start gap-5 rounded-2.5xl border border-line bg-white p-7 text-left shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-brand-200 hover:shadow-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
            key={module.title}
            onClick={() => onModuleChange(key)}
            type="button"
          >
            <div>
              <h2 className="text-lg font-semibold leading-6 text-ink">{module.title}</h2>
              <p className="mt-2 max-w-[230px] text-[13px] leading-[21px] text-muted">
                {module.desc}
              </p>
            </div>
          </button>
        );
      })}
    </section>
  );
}
