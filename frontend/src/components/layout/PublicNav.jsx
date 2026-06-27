import Logo from "./Logo";
import { navItems } from "./navigationData";

export default function PublicNav({ onEnterWorkbench, onEnterChatDemo }) {
  return (
    <header className="fixed left-0 right-0 top-0 z-40 px-4 pt-6 sm:px-8">
      <div className="mx-auto flex h-16 max-w-[1232px] items-center justify-between rounded-full border border-line bg-white px-6 shadow-nav">
        <Logo />

        <nav className="hidden items-center gap-4 lg:flex">
          {navItems.map((item) => (
            <div className="group relative" key={item.label}>
              <button
                className={`h-[34px] rounded-full border px-5 text-sm font-medium transition-colors ${
                  item.label === "AI Agent"
                    ? "border-ink bg-ink text-white"
                    : "border-line bg-page text-slate-600 hover:border-brand-100 hover:text-ink"
                }`}
                type="button"
              >
                {item.label}
              </button>
              <div className="invisible absolute left-1/2 top-10 w-44 -translate-x-1/2 rounded-2xl border border-line bg-white p-2 opacity-0 shadow-card transition-all duration-200 group-hover:visible group-hover:translate-y-1 group-hover:opacity-100">
                {item.items.map((child) => (
                  <a
                    className="block rounded-xl px-3 py-1.5 text-sm text-slate-600 hover:bg-brand-50 hover:text-brand-700"
                    href="#hero"
                    key={child}
                  >
                    {child}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            className="inline-flex h-[38px] items-center rounded-full border border-brand-200 bg-brand-50 px-4 text-sm font-semibold text-brand-600 transition-colors hover:bg-brand-100 sm:hidden"
            onClick={onEnterChatDemo}
            type="button"
          >
            体验
          </button>
          <button
            className="hidden h-[38px] rounded-full border border-brand-200 bg-brand-50 px-6 text-sm font-semibold text-brand-600 transition-colors hover:bg-brand-100 sm:inline-flex sm:items-center"
            onClick={onEnterChatDemo}
            type="button"
          >
            C端体验
          </button>
          <button
            className="hidden h-[38px] rounded-full border border-line bg-white px-6 text-sm font-semibold text-ink shadow-sm transition-all hover:border-brand-200 hover:shadow-card sm:inline-flex sm:items-center"
            onClick={onEnterWorkbench}
            type="button"
          >
            登录
          </button>
          <button
            className="inline-flex h-[38px] items-center rounded-full bg-brand-600 px-4 text-sm font-semibold text-white shadow-button-primary transition-all hover:-translate-y-0.5 hover:bg-brand-700 hover:shadow-button-primary-hover sm:px-6"
            onClick={onEnterWorkbench}
            type="button"
          >
            <span className="sm:hidden">工作台</span>
            <span className="hidden sm:inline">免费试用</span>
          </button>
        </div>
      </div>
    </header>
  );
}
