export function ChatBubble({ citations = [], content, role, streaming = false, timestamp }) {
  if (role === "user") {
    return (
      <div className="flex justify-end animate-fade-in-up">
        <div className="max-w-[85%] rounded-2xl bg-gradient-to-br from-brand-600 to-brand-700 px-5 py-3 shadow-sm sm:max-w-[75%]">
          <p className="text-sm leading-6 text-white">{content}</p>
          <p className="mt-1 text-right text-[11px] text-brand-200/80">{timestamp}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 animate-fade-in-up">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 shadow-sm">
        <svg aria-hidden="true" className="h-3.5 w-3.5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <div className="max-w-[88%] rounded-2xl border border-line bg-white px-5 py-3 shadow-sm sm:max-w-[85%]">
        <p className="text-sm leading-6 text-slate-700">
          {content}
          {streaming && (
            <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-brand-500 align-middle" />
          )}
        </p>
        <p className="mt-1 text-[11px] text-slate-400">{timestamp}</p>
      </div>
    </div>
  );
}
