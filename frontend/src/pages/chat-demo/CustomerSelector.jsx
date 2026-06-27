export function CustomerSelector({ customers, selectedId, onChange, loading }) {
  const selected = customers.find((c) => c.customer_id === selectedId);

  return (
    <div className="border-b border-line bg-white px-4 py-2.5 sm:px-8">
      <div className="mx-auto flex max-w-[720px] items-center gap-3">
        <label className="text-xs font-semibold text-slate-400 shrink-0">模拟客户</label>
        {loading ? (
          <div className="h-9 w-full animate-pulse rounded-full bg-slate-100" />
        ) : (
          <select
            className="h-9 flex-1 rounded-full border border-line bg-page px-3 text-sm text-slate-700 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 transition-colors"
            onChange={(e) => onChange(e.target.value)}
            value={selectedId ?? ""}
          >
            <option disabled value="">
              请选择一位模拟客户
            </option>
            {customers.map((customer) => (
              <option key={customer.customer_id} value={customer.customer_id}>
                {customer.name} · {customer.plan} {customer.is_vip ? "· VIP" : ""}
              </option>
            ))}
          </select>
        )}
        {selected ? (
          <span className="flex shrink-0 items-center gap-1.5 text-xs text-slate-400">
            {selected.is_vip ? (
              <span className="inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">VIP</span>
            ) : null}
            <span className="hidden sm:inline">{selected.plan}</span>
          </span>
        ) : null}
      </div>
    </div>
  );
}
