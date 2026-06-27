export default function Logo() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 via-sky-500 to-cyan-400 text-xs font-bold text-white shadow-glow">
        AI
      </div>
      <span className="text-sm font-semibold text-ink">SupportPilot AI</span>
    </div>
  );
}
