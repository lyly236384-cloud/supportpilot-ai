export function StatusChip({ children, tone = "neutral" }) {
  const classes = {
    danger: "border-red-200 bg-red-50 text-red-600",
    warning: "border-orange-200 bg-orange-50 text-orange-600",
    success: "border-emerald-200 bg-emerald-50 text-emerald-600",
    info: "border-blue-200 bg-blue-50 text-brand-600",
    neutral: "border-slate-200 bg-slate-50 text-slate-600",
    dark: "border-ink bg-ink text-white",
  };

  return (
    <span
      className={`inline-flex h-6 items-center justify-center rounded-full border px-3 text-xs font-semibold ${classes[tone] ?? classes.neutral}`}
    >
      {children}
    </span>
  );
}
