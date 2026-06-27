import { displayMetric, formatRate } from "./shared/formatters";

function LiquidGlassMark() {
  return (
    <div aria-hidden="true" className="relative h-36 w-52 max-lg:hidden">
      <div className="absolute left-3 top-6 h-20 w-36 rotate-12 rounded-[50%] bg-gradient-to-br from-sky-100/90 via-blue-400/70 to-blue-700/40 blur-[1px] shadow-glow" />
      <div className="absolute right-3 top-3 h-10 w-16 rotate-[18deg] rounded-[50%] bg-gradient-to-br from-white to-slate-200/80" />
      <div className="absolute left-14 top-8 h-9 w-14 rotate-12 rounded-[50%] bg-gradient-to-br from-white/80 to-blue-400/70" />
      <div className="absolute bottom-6 left-12 h-3 w-24 rotate-12 rounded-full bg-gradient-to-r from-white/90 to-blue-500/30 shadow-glow" />
    </div>
  );
}

export function WorkbenchHero({ metrics, loading = false }) {
  const total = displayMetric(metrics?.total_conversations, loading);
  const autoReply = displayMetric(metrics?.auto_reply_count, loading);
  const handoff = displayMetric(metrics?.handoff_count, loading);
  const tickets = displayMetric(metrics?.ticket_count, loading);
  const autoRate = loading ? "—" : formatRate(metrics?.auto_resolution_rate);

  const stats = [
    ["咨询总量", total],
    ["AI 自动处理", autoReply],
    ["转人工", handoff],
    ["服务工单", tickets],
  ];

  return (
    <section className="mx-auto flex w-full max-w-[1232px] rounded-4xl bg-gradient-to-r from-brand-900 via-brand-600 to-sky-400 px-8 py-9 text-white shadow-card sm:px-10 lg:min-h-[390px]">
      <div className="grid w-full gap-8 lg:grid-cols-[minmax(0,1fr)_520px] lg:items-start">
        <div>
          <p className="text-xs font-semibold uppercase leading-[18px] text-blue-200">
            SupportPilot AI 服务操作系统
          </p>
          <h1 className="mt-5 max-w-[720px] text-[30px] font-semibold leading-[38px]">
            客服问题、人工队列、工单与知识库，在这里形成一个可运营的闭环。
          </h1>
          <p className="mt-4 max-w-[620px] text-sm leading-[22px] text-blue-100">
            累计 {total} 次咨询，{autoReply} 次自动处理，{handoff} 次转人工，{tickets} 条服务工单；AI 自动解决率 {autoRate}。（数据来自 /api/metrics）
          </p>
        </div>

        <div className="flex items-start justify-between gap-8">
          <div className="mt-28 grid grid-cols-2 gap-6 sm:grid-cols-4 max-lg:mt-0">
            {stats.map(([label, value]) => (
              <div key={label}>
                <p className="text-2xl font-semibold leading-[30px]">{value}</p>
                <p className="mt-1 text-xs leading-[18px] text-blue-200">{label}</p>
              </div>
            ))}
          </div>
          <LiquidGlassMark />
        </div>
      </div>
    </section>
  );
}
