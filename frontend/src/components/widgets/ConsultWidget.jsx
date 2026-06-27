import { useState } from "react";
import { createPortal } from "react-dom";
import { useProductChat } from "../../hooks/useProductChat";

export default function ConsultWidget() {
  const { messages, pending, error, send } = useProductChat();
  const [input, setInput] = useState("");
  const [open, setOpen] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    const text = input;
    setInput("");
    await send(text);
  }

  const widget = (
    <>
      <button
        aria-label="打开在线咨询"
        className="fixed z-[100] hidden h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-white shadow-button-primary transition-all hover:-translate-y-0.5 hover:bg-brand-700 hover:shadow-button-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 lg:flex"
        style={{ right: "20px", bottom: "20px" }}
        onClick={() => setOpen(true)}
        type="button"
      >
        <svg aria-hidden="true" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
          <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span className="absolute right-0.5 top-0.5 h-3 w-3 rounded-full bg-emerald-500 ring-2 ring-white" />
      </button>

      {open ? (
        <aside className="fixed z-[100] w-80 select-none rounded-3xl border border-line bg-white shadow-modal" style={{ right: "20px", bottom: "90px" }}>
          <div className="flex items-center justify-between gap-2 rounded-t-3xl border-b border-line px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-emerald-500" />
              <div>
                <p className="text-sm font-semibold text-ink">在线咨询</p>
                <p className="text-xs text-muted">了解产品能力和适用场景</p>
              </div>
            </div>
            <button
              aria-label="收起咨询窗口"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
              onClick={() => setOpen(false)}
              type="button"
            >
              <svg aria-hidden="true" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path d="M5 12h14" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>

          <div className="p-4">
            <div className="max-h-56 space-y-2 overflow-y-auto">
              {messages.map((message, index) => (
                <div
                  className={`rounded-2xl px-3 py-2 text-sm leading-6 ${
                    message.role === "user"
                      ? "ml-6 bg-brand-600 text-white"
                      : "bg-slate-50 text-slate-700"
                  }`}
                  key={`${message.role}-${index}`}
                >
                  {message.content}
                </div>
              ))}
              {pending ? <p className="text-xs text-slate-500">正在生成回复…</p> : null}
              {error ? <p className="text-xs text-red-600">{error}</p> : null}
            </div>

            <form className="mt-3 flex gap-2" onSubmit={handleSubmit}>
              <input
                className="h-10 min-w-0 flex-1 rounded-full border border-line px-3 text-sm outline-none transition focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
                disabled={pending}
                onChange={(event) => setInput(event.target.value)}
                placeholder="输入问题"
                value={input}
              />
              <button
                className="h-10 rounded-full bg-ink px-4 text-sm font-semibold text-white transition-colors hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-60"
                disabled={pending || !input.trim()}
                type="submit"
              >
                发送
              </button>
            </form>
          </div>
        </aside>
      ) : null}
    </>
  );

  if (typeof document === "undefined") {
    return null;
  }

  return createPortal(widget, document.body);
}
