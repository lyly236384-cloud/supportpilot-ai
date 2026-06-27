import Logo from "../../components/layout/Logo";

export function ChatDemoNav({ onBackHome }) {
  return (
    <header className="shrink-0 px-4 pt-4 sm:px-8">
      <div className="mx-auto flex h-[60px] max-w-[1232px] items-center justify-between rounded-full border border-line bg-white px-6 shadow-nav">
        <div className="flex items-center gap-3">
          <Logo />
          <span className="hidden text-sm font-medium text-slate-300 sm:inline">|</span>
          <span className="text-sm font-medium text-slate-500">客服体验 Demo</span>
        </div>
        <button
          className="h-9 rounded-full border border-line bg-white px-4 text-sm font-medium text-slate-600 transition-all hover:border-brand-200 hover:text-brand-600 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
          onClick={onBackHome}
          type="button"
        >
          ← 返回首页
        </button>
      </div>
    </header>
  );
}
