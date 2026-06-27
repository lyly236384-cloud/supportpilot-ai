import { EmptyState } from "./EmptyState";

export function DataTable({
  rows,
  columns,
  renderRow,
  emptyTitle,
  onRowClick,
  selectedRowId,
  getRowId,
  gridTemplate,
}) {
  const resolveRowId = (row) => getRowId?.(row) ?? row.id ?? row.trace_id ?? row.ticket_id ?? row.title;
  const templateStyle = gridTemplate ? { gridTemplateColumns: gridTemplate } : undefined;

  if (!rows.length) {
    return <EmptyState title={emptyTitle} />;
  }

  return (
    <div className="space-y-3">
      <div
        className="grid gap-3 px-4 text-xs font-semibold text-slate-500"
        style={templateStyle}
      >
        {columns.map((column) => (
          <span key={column}>{column}</span>
        ))}
      </div>
      <div className="space-y-3">
        {rows.slice(0, 8).map((row) => {
          const rowId = resolveRowId(row);
          const selected = selectedRowId === rowId;

          return (
            <button
              className={`grid min-h-12 w-full gap-3 rounded-2xl border px-4 py-3 text-left text-sm text-slate-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-1 ${
                selected
                  ? "border-brand-200 bg-brand-50"
                  : "border-line bg-white hover:border-brand-200 hover:bg-brand-50/50"
              } ${onRowClick ? "cursor-pointer" : "cursor-default"}`}
              key={rowId}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              style={templateStyle}
              type="button"
            >
              {renderRow(row).map((cell, index) => (
                <span className="min-w-0 truncate" key={`${rowId}-${index}`}>
                  {cell}
                </span>
              ))}
            </button>
          );
        })}
      </div>
    </div>
  );
}
