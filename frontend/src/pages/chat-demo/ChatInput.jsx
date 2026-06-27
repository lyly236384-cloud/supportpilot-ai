import { useRef, useEffect } from "react";

export function ChatInput({ pending, demoCases, onSend, onDemoSelect }) {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (!pending && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [pending]);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      const message = textareaRef.current?.value.trim();
      if (message) {
        onSend(message);
        textareaRef.current.value = "";
        textareaRef.current.style.height = "auto";
      }
    }
  }

  function handleInput(e) {
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
  }

  function handleClickSend() {
    const message = textareaRef.current?.value.trim();
    if (message) {
      onSend(message);
      textareaRef.current.value = "";
      textareaRef.current.style.height = "auto";
    }
  }

  return (
    <div className="border-t border-line bg-white px-4 pb-5 pt-3 sm:px-8">
      <div className="mx-auto max-w-[720px]">
        {demoCases?.length ? (
          <div className="mb-3 flex gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible sm:pb-0">
            {demoCases.map((demo) => (
              <button
                className="shrink-0 truncate rounded-full border border-line bg-page px-3.5 py-1.5 text-xs font-medium text-slate-500 transition-all hover:border-brand-300 hover:bg-brand-50 hover:text-brand-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-1"
                key={demo.message}
                onClick={() => onDemoSelect(demo)}
                title={demo.message}
                type="button"
              >
                {demo.message.length > 18 ? demo.message.slice(0, 18) + "…" : demo.message}
              </button>
            ))}
          </div>
        ) : null}

        <div className="flex items-end gap-3">
          <textarea
            className="min-h-[44px] max-h-[120px] flex-1 resize-none rounded-2xl border border-line bg-page px-4 py-2.5 text-sm leading-6 text-slate-700 placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100 transition-colors disabled:opacity-60"
            disabled={pending}
            onInput={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="输入您的问题…"
            ref={textareaRef}
            rows={1}
          />
          <button
            aria-label="发送"
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white shadow-button-primary transition-all hover:-translate-y-0.5 hover:bg-brand-700 hover:shadow-button-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2 disabled:opacity-40 disabled:hover:translate-y-0"
            disabled={pending}
            onClick={handleClickSend}
            type="button"
          >
            <svg aria-hidden="true" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
