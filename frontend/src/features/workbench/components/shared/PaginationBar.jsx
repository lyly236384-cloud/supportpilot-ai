export const DEFAULT_PAGE_SIZE = 15;

export function PaginationBar({ offset, limit, total, onPageChange, loading = false }) {
  const safeLimit = Math.max(1, limit || DEFAULT_PAGE_SIZE);
  const currentPage = Math.floor(offset / safeLimit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / safeLimit));
  const canPrev = offset > 0;
  const canNext = offset + safeLimit < total;

  return (
    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-line bg-slate-50 px-4 py-3">
      <p className="text-sm text-slate-600">
        第 {currentPage} / {totalPages} 页，共 {total} 条
      </p>
      <div className="flex gap-2">
        <button
          className="h-9 rounded-full border border-line bg-white px-4 text-sm font-semibold text-slate-700 disabled:opacity-50"
          disabled={loading || !canPrev}
          onClick={() => onPageChange(Math.max(0, offset - safeLimit))}
          type="button"
        >
          上一页
        </button>
        <button
          className="h-9 rounded-full border border-line bg-white px-4 text-sm font-semibold text-slate-700 disabled:opacity-50"
          disabled={loading || !canNext}
          onClick={() => onPageChange(offset + safeLimit)}
          type="button"
        >
          下一页
        </button>
      </div>
    </div>
  );
}
