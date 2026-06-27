import { lazy, Suspense, useRef } from "react";
import PublicNav from "../../components/layout/PublicNav";
import ConsultWidget from "../../components/widgets/ConsultWidget";
import HomeLiveMetrics from "../../components/widgets/HomeLiveMetrics";

const ColorBends = lazy(() => import("../../components/ColorBends/ColorBends"));
const SkillsShowcase = lazy(() =>
  import("../../features/skills-showcase/components/SkillsShowcase")
);

function HomeHero({ onEnterWorkbench, onEnterChatDemo }) {
  const heroRef = useRef(null);

  return (
    <section
      className="relative flex min-h-screen items-center justify-center overflow-hidden bg-page px-5 pb-24 pt-40"
      id="hero"
      ref={heroRef}
    >
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 z-0">
        <Suspense fallback={<div className="h-full w-full bg-blue-50" />}>
          <ColorBends
            autoRotate={0}
            bandWidth={5}
            colors={["#2563eb", "#38bdf8", "#8b5cf6"]}
            frequency={1}
            intensity={1.15}
            iterations={1}
            mouseInfluence={0.75}
            noise={0.1}
            parallax={0.45}
            pointerContainerRef={heroRef}
            rotation={90}
            scale={1}
            speed={0.2}
            transparent
            warpStrength={1}
          />
        </Suspense>
        <div className="absolute inset-0 bg-gradient-to-b from-white/88 via-white/76 to-page" />
      </div>

      <div className="relative z-10 mx-auto flex w-full max-w-[1232px] flex-col items-center text-center">
        <div className="inline-flex h-8 items-center rounded-full border border-blue-200 bg-blue-50 px-16 text-sm font-semibold text-brand-600 max-sm:px-6">
          面向企业服务团队的 AI Agent 工作台
        </div>

        <h1 className="mt-16 max-w-[1000px] text-[44px] font-semibold leading-[1.15] tracking-normal text-ink sm:text-[56px] lg:text-[62px]">
          让每一次服务，都能妥善承接
        </h1>

        <p className="mt-8 max-w-[764px] text-lg leading-8 text-slate-600">
          SupportPilot AI 将标准问题快速回应，将复杂需求持续跟进。
        </p>

        <div className="mt-10 flex flex-col gap-5 sm:flex-row">
          <button
            className="inline-flex h-11 items-center justify-center rounded-full bg-ink px-12 text-sm font-semibold text-white shadow-card transition-all hover:-translate-y-0.5 hover:shadow-card-hover"
            onClick={onEnterChatDemo}
            type="button"
          >
            体验客服
          </button>
          <button
            className="inline-flex h-11 items-center justify-center rounded-full bg-brand-600 px-12 text-sm font-semibold text-white shadow-button-primary transition-all hover:-translate-y-0.5 hover:bg-brand-700 hover:shadow-button-primary-hover"
            onClick={onEnterWorkbench}
            type="button"
          >
            进入工作台
          </button>
        </div>
      </div>

    </section>
  );
}

export default function HomePage({ onEnterWorkbench, onEnterChatDemo }) {
  return (
    <>
      <PublicNav onEnterWorkbench={onEnterWorkbench} onEnterChatDemo={onEnterChatDemo} />
      <main>
        <HomeHero onEnterWorkbench={onEnterWorkbench} onEnterChatDemo={onEnterChatDemo} />
        <Suspense fallback={<div className="h-96 bg-page" />}>
          <SkillsShowcase
            onEnterChatDemo={onEnterChatDemo}
            onEnterWorkbench={onEnterWorkbench}
          />
        </Suspense>
        <HomeLiveMetrics />
      </main>
      <ConsultWidget />
    </>
  );
}
