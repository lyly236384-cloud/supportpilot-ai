export const moduleKeys = ["overview", "queue", "records", "tickets", "knowledge"];

export const moduleMeta = {
  overview: {
    title: "数据概览",
    desc: "从 /api/metrics 与处理记录中同步运营指标，帮助管理者判断当前服务压力。",
    glyph: "D",
    color: "blue",
  },
  queue: {
    title: "人工队列",
    desc: "集中处理需要人工判断、升级或持续跟进的客户请求。",
    glyph: "Q",
    color: "orange",
  },
  records: {
    title: "处理记录",
    desc: "展示所有 AI 工作流记录：意图、知识、动作、风险与最终结果。",
    glyph: "R",
    color: "cyan",
  },
  tickets: {
    title: "服务工单",
    desc: "把需要持续跟进的复杂需求沉淀为可分配、可追踪、可复盘的服务工单。",
    glyph: "T",
    color: "emerald",
  },
  knowledge: {
    title: "知识库",
    desc: "维护可被 AI 引用的业务规则，让每次回答都有来源、可更新、可审计。",
    glyph: "K",
    color: "indigo",
  },
};
