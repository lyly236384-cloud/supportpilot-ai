import { skills } from "../data/skills";

function SkillIcon({ label, accent }) {
  return (
    <div
      aria-hidden="true"
      className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${accent} text-sm font-semibold text-white shadow-sm transition-transform duration-300 group-hover:scale-105`}
    >
      {label.slice(0, 2)}
    </div>
  );
}

function SkillCard({ skill }) {
  return (
    <article
      aria-label={`${skill.tag} · ${skill.title}`}
      className="group relative overflow-hidden rounded-2.5xl border border-line bg-white p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-brand-600 hover:shadow-card-hover sm:p-7"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-brand-600 to-cyan-500 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="flex items-start justify-between gap-4">
        <SkillIcon label={skill.tag} accent={skill.accent} />
        <span className="rounded-full bg-page px-3 py-1 text-xs font-medium text-slate-600 transition-colors duration-300 group-hover:bg-brand-600 group-hover:text-white">
          {skill.metric}
        </span>
      </div>
      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-600">{skill.tag}</p>
        <h3 className="mt-2 text-xl font-semibold leading-7 text-ink">{skill.title}</h3>
        <p className="mt-3 text-[15px] leading-7 text-muted">{skill.desc}</p>
      </div>
    </article>
  );
}

export default function SkillsShowcase({ onEnterWorkbench, onEnterChatDemo }) {
  return (
    <section className="bg-page px-5 py-16 sm:px-8 lg:px-20 lg:py-24" id="features">
      <div className="mx-auto max-w-[1180px]">
        <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-600">
              产品能力
            </p>
            <h2 className="mt-4 text-3xl font-semibold leading-tight text-ink sm:text-4xl lg:text-5xl">
              把 AI 接待、人工协同和服务数据放进同一个客服运营闭环
            </h2>
            <p className="mt-5 text-base leading-8 text-muted sm:text-lg">
              面向企业客服团队，覆盖客户问题识别、AI 处理、转人工、工单跟进和运营分析，帮助管理者看清服务效率与知识缺口。
            </p>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:mt-12 lg:grid-cols-3 lg:gap-5">
          {skills.map((skill) => (
            <SkillCard key={skill.title} skill={skill} />
          ))}
        </div>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            className="inline-flex h-12 items-center justify-center rounded-full bg-brand-600 px-6 text-sm font-semibold text-white shadow-button-primary transition-all duration-200 hover:-translate-y-0.5 hover:bg-brand-700 hover:shadow-button-primary-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-4"
            onClick={onEnterWorkbench}
            type="button"
          >
            进入工作台
          </button>
          {onEnterChatDemo ? (
            <button
              className="inline-flex h-12 items-center justify-center rounded-full px-6 text-sm font-semibold text-slate-700 transition-colors duration-200 hover:text-brand-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-4"
              onClick={onEnterChatDemo}
              type="button"
            >
              先体验客服对话 →
            </button>
          ) : null}
        </div>
      </div>
    </section>
  );
}
