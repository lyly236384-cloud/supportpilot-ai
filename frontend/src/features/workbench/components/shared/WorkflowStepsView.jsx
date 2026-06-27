import { WORKFLOW_STEP_STATUS_LABELS } from "../../utils/normalizeTrace";

export function WorkflowStepsView({ steps = [], compact = false }) {
  if (!steps.length) {
    return <p className="text-sm text-slate-500">暂无工作流步骤。</p>;
  }

  if (compact) {
    return (
      <ol className="relative border-l-2 border-slate-100 ml-2 space-y-4">
        {steps.map((step, index) => (
          <li className="relative pl-5" key={`${step.name}-${index}`}>
            <span className="absolute -left-[5px] top-1.5 h-2 w-2 rounded-full bg-brand-500 ring-2 ring-white" />
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-slate-700">{step.name}</p>
              <span className="text-[10px] text-slate-400">
                {WORKFLOW_STEP_STATUS_LABELS[step.status] ?? step.status}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-600">{step.summary}</p>
            {step.detail ? <p className="mt-0.5 text-[11px] leading-5 text-slate-400">{step.detail}</p> : null}
          </li>
        ))}
      </ol>
    );
  }

  return (
    <ol className="space-y-3">
      {steps.map((step, index) => (
        <li className="rounded-2xl border border-slate-100 bg-white p-4" key={`${step.name}-${index}`}>
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-ink">{step.name}</p>
            <span className="text-xs font-medium text-slate-500">
              {WORKFLOW_STEP_STATUS_LABELS[step.status] ?? step.status}
            </span>
          </div>
          <p className="mt-2 text-sm text-slate-700">{step.summary}</p>
          {step.detail ? <p className="mt-2 text-xs leading-6 text-slate-500">{step.detail}</p> : null}
        </li>
      ))}
    </ol>
  );
}
