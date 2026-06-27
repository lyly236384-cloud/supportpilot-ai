# 网站技能展示板块重构方案

适用前提：React + Tailwind，已有 `pages/` 和 `components/` 目录，不新增外部依赖。

## 1. Figma 画板结构

### Desktop Frame

- Frame：`Section/SkillsShowcase/Desktop`
- 尺寸：`1440 x auto`
- 背景：`#F6F8FB`
- 内边距：左右 `80`，上下 `96`
- 最大内容宽度：`1180`

图层结构：

```text
Section/SkillsShowcase/Desktop
  Container
    Header
      Eyebrow
      Title
      Description
    FeatureGrid
      SkillCard/TextAI
      SkillCard/Routing
      SkillCard/KnowledgeBase
      SkillCard/HumanHandoff
      SkillCard/Ticketing
      SkillCard/Analytics
    FooterAction
      PrimaryButton
      SecondaryLink
```

### Mobile Frame

- Frame：`Section/SkillsShowcase/Mobile`
- 尺寸：`375 x auto`
- 背景：`#F6F8FB`
- 内边距：左右 `20`，上下 `64`
- 布局：单列卡片，间距 `14`

### 可复用组件

组件名：`Component/SkillCard`

变体：

- `state=default`
- `state=hover`
- `state=active`

卡片尺寸：

- Desktop：`min-height 220`，圆角 `20`
- Mobile：`min-height 180`，圆角 `18`
- Padding：desktop `28`，mobile `22`
- Border：`1px #DCE4EF`
- Hover border：`#2563EB`
- Hover shadow：`0 24px 60px rgba(15, 23, 42, 0.12)`

图层命名规范：

- 页面区块：`Section/模块名/端`
- 组件：`Component/组件名`
- 卡片实例：`SkillCard/功能名`
- 文本：`Text/Title`、`Text/Description`、`Text/Meta`
- 状态层：`State/HoverOverlay`

## 2. UI/UX Pro Max 优化

### 信息层级

1. 先说明产品能力主题：AI 客服平台的核心能力，而不是泛泛展示技术栈。
2. 再展示 6 个能力卡片：文本 AI、智能分流、知识库、人工协同、服务工单、数据分析。
3. 每张卡片只表达一个业务价值：减少人工压力、提升响应质量、沉淀服务数据。
4. CTA 放在板块底部，引导进入工作台或免费试用，不抢卡片主信息。

### Hover 交互

- 卡片 hover：上移 `-4px`，边框变主色，阴影增强。
- 卡片内部标识 hover：背景从浅蓝变深蓝，文字变白。
- CTA hover：主按钮轻微上移，增加阴影。
- 移动端不依赖 hover，只保留点击反馈和清晰间距。

### 全局设计系统

颜色：

- Primary：`#2563EB`
- Primary dark：`#1D4ED8`
- Ink：`#0F172A`
- Muted：`#64748B`
- Surface：`#FFFFFF`
- Page：`#F6F8FB`
- Border：`#DCE4EF`
- Accent cyan：`#06B6D4`
- Accent amber：`#F59E0B`

字体阶梯：

- Display：`48/56, font-semibold`
- H2：`36/44, font-semibold`
- H3：`20/28, font-semibold`
- Body：`16/26, font-normal`
- Caption：`13/20, font-medium`

间距：

- Section padding：desktop `96px 80px`，mobile `64px 20px`
- Grid gap：desktop `20px`，mobile `14px`
- Card padding：desktop `28px`，mobile `22px`
- 内部元素间距：`8 / 12 / 16 / 24`

圆角与阴影：

- Card radius：`20px`
- Button radius：`999px`
- Badge radius：`999px`
- Default shadow：`0 16px 40px rgba(15, 23, 42, 0.08)`
- Hover shadow：`0 24px 60px rgba(15, 23, 42, 0.12)`

## 3. Frontend Design 组件代码

建议路径：

- `src/features/skills-showcase/components/SkillsShowcase.jsx`
- 在首页 `src/pages/home/HomePage.jsx` 中引入 `<SkillsShowcase />`

```jsx
const skills = [
  {
    tag: "Text AI",
    title: "文本 AI 接待",
    desc: "识别客户意图，结合知识库生成可追踪的回复建议，减少重复咨询压力。",
    metric: "7x24 响应",
    accent: "from-blue-600 to-cyan-500",
  },
  {
    tag: "Routing",
    title: "智能分流",
    desc: "按问题类型、紧急程度和处理状态分配到 AI 或人工队列。",
    metric: "自动判定",
    accent: "from-indigo-600 to-blue-500",
  },
  {
    tag: "Knowledge",
    title: "知识库",
    desc: "沉淀产品、售后、政策和流程资料，为 AI 回复和人工处理提供依据。",
    metric: "统一资料源",
    accent: "from-cyan-600 to-emerald-500",
  },
  {
    tag: "Handoff",
    title: "人工协同",
    desc: "AI 无法解决的问题自动转人工，并保留客户上下文与处理摘要。",
    metric: "上下文交接",
    accent: "from-violet-600 to-indigo-500",
  },
  {
    tag: "Ticket",
    title: "服务工单",
    desc: "将复杂问题沉淀为工单，跟踪处理进度、责任人和最终结果。",
    metric: "闭环跟进",
    accent: "from-amber-500 to-orange-500",
  },
  {
    tag: "Analytics",
    title: "数据分析",
    desc: "汇总 AI 解决率、转人工原因、热点问题和知识缺口，辅助管理决策。",
    metric: "运营可视化",
    accent: "from-slate-700 to-blue-600",
  },
];

function SkillIcon({ label, accent }) {
  return (
    <div className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${accent} text-sm font-semibold text-white shadow-lg shadow-slate-200 transition-transform duration-300 group-hover:scale-105`}>
      {label.slice(0, 2)}
    </div>
  );
}

function SkillCard({ skill }) {
  return (
    <article className="group relative overflow-hidden rounded-[20px] border border-[#DCE4EF] bg-white p-6 shadow-[0_16px_40px_rgba(15,23,42,0.08)] transition-all duration-300 hover:-translate-y-1 hover:border-[#2563EB] hover:shadow-[0_24px_60px_rgba(15,23,42,0.12)] sm:p-7">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-hover:from-blue-600 group-hover:to-cyan-500" />
      <div className="flex items-start justify-between gap-4">
        <SkillIcon label={skill.tag} accent={skill.accent} />
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 transition-colors duration-300 group-hover:bg-blue-600 group-hover:text-white">
          {skill.metric}
        </span>
      </div>
      <div className="mt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-600">{skill.tag}</p>
        <h3 className="mt-2 text-xl font-semibold leading-7 text-slate-950">{skill.title}</h3>
        <p className="mt-3 text-[15px] leading-7 text-slate-600">{skill.desc}</p>
      </div>
      <div className="mt-6 h-px bg-slate-100" />
      <button className="mt-5 text-sm font-semibold text-slate-900 transition-colors duration-200 hover:text-blue-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-4">
        查看能力说明
      </button>
    </article>
  );
}

export default function SkillsShowcase() {
  return (
    <section className="bg-[#F6F8FB] px-5 py-16 sm:px-8 lg:px-20 lg:py-24">
      <div className="mx-auto max-w-[1180px]">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">Product capabilities</p>
          <h2 className="mt-4 text-3xl font-semibold leading-tight text-slate-950 sm:text-4xl lg:text-5xl">
            把 AI 接待、人工协同和服务数据放进同一个客服运营闭环
          </h2>
          <p className="mt-5 text-base leading-8 text-slate-600 sm:text-lg">
            面向企业客服团队，覆盖客户问题识别、AI 处理、转人工、工单跟进和运营分析，帮助管理者看清服务效率与知识缺口。
          </p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:mt-12 lg:grid-cols-3 lg:gap-5">
          {skills.map((skill) => (
            <SkillCard key={skill.title} skill={skill} />
          ))}
        </div>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
          <a className="inline-flex h-12 items-center justify-center rounded-full bg-blue-600 px-6 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(37,99,235,0.28)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-4" href="/workspace">
            进入工作台
          </a>
          <a className="inline-flex h-12 items-center justify-center rounded-full px-6 text-sm font-semibold text-slate-700 transition-colors duration-200 hover:text-blue-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-4" href="#contact">
            了解接入方式
          </a>
        </div>
      </div>
    </section>
  );
}
```

## 4. 首页接入示例

```jsx
import SkillsShowcase from "../../features/skills-showcase/components/SkillsShowcase";

export default function HomePage() {
  return (
    <main>
      {/* existing hero */}
      <SkillsShowcase />
      {/* existing sections */}
    </main>
  );
}
```

## 5. 验收标准

- Desktop：三列卡片，标题说明和 CTA 不拥挤。
- Tablet：两列卡片，卡片高度基本一致。
- Mobile：单列卡片，无横向滚动，按钮可点击区域不低于 `44px`。
- Hover：卡片上移、边框变蓝、阴影增强。
- 无新增依赖，无图片资源依赖。
- 文案不写“作品集”“Demo”“面试官”，保持真实 B 端产品表达。
