export function EmptyState({ title, desc, className = "" }) {
  return (
    <div
      className={`rounded-2.5xl border border-dashed border-line bg-page px-5 py-10 text-center ${className}`}
    >
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted">
        {desc ?? "当前接口返回为空，后续有业务记录后会自动展示。"}
      </p>
    </div>
  );
}
