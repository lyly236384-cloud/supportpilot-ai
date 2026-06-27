export function FilterBar({ filters, fields, onChange, onReset, loading = false }) {
  return (
    <div className="mt-6 rounded-2xl border border-line bg-page p-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {fields.map((field) => (
          <label className="block" key={field.key}>
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
              {field.label}
            </span>
            {field.options ? (
              <select
                className="mt-2 h-11 w-full rounded-2xl border border-line bg-white px-4 text-sm outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                disabled={loading}
                onChange={(event) => onChange(field.key, event.target.value)}
                value={filters[field.key] ?? ""}
              >
                <option value="">全部</option>
                {field.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                className="mt-2 h-11 w-full rounded-2xl border border-line bg-white px-4 text-sm outline-none transition-colors focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
                disabled={loading}
                onChange={(event) => onChange(field.key, event.target.value)}
                placeholder={field.placeholder ?? ""}
                value={filters[field.key] ?? ""}
              />
            )}
          </label>
        ))}
      </div>
      <div className="mt-4 flex justify-end">
        <button
          className="h-10 rounded-full border border-line bg-white px-4 text-sm font-semibold text-slate-700 transition-colors hover:border-brand-200 hover:text-brand-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-50"
          disabled={loading}
          onClick={onReset}
          type="button"
        >
          重置筛选
        </button>
      </div>
    </div>
  );
}
