export function CitationsView({ citations = [] }) {
  if (!citations.length) {
    return <p className="text-sm text-slate-500">暂无知识库引用。</p>;
  }

  return (
    <ul className="space-y-2">
      {citations.map((citation, index) => (
        <li
          className="rounded-xl border border-slate-100 bg-slate-50/50 p-3"
          key={`${citation.source}-${index}`}
        >
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-semibold text-slate-700 truncate">{citation.source}</p>
            <span className="shrink-0 text-[10px] text-slate-400">
              score {typeof citation.score === "number" ? citation.score.toFixed(2) : citation.score}
            </span>
          </div>
          <p className="mt-1.5 text-xs leading-5 text-slate-500">{citation.snippet}</p>
        </li>
      ))}
    </ul>
  );
}
