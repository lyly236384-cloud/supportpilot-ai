import { useState } from "react";
import Logo from "../../components/layout/Logo";
import {
  DebugDrawer,
  WorkbenchHero,
  WorkbenchModuleNav,
  WorkbenchPanel,
} from "../../features/workbench/components";
import { moduleMeta } from "../../features/workbench/components/moduleMeta";
import { useWorkbenchData } from "../../features/workbench/hooks/useWorkbenchData";
import { useSupportChat } from "../../hooks/useSupportChat";

const topNav = ["员工中心", "客服管理", "系统管理"];

function ProductNav({ onBackHome }) {
  return (
    <header className="px-4 pt-8 sm:px-8">
      <div className="mx-auto flex h-[74px] max-w-[1232px] items-center rounded-full border border-line bg-white px-8 shadow-nav gap-16">
        <button
          className="shrink-0 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
          onClick={onBackHome}
          type="button"
        >
          <Logo />
        </button>
        <nav className="hidden items-center gap-8 md:flex">
          {topNav.map((item) => (
            <button
              className="text-sm font-medium text-slate-500 transition-colors hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
              key={item}
              type="button"
            >
              {item}
            </button>
          ))}
        </nav>
        <button
          aria-label="返回首页"
          className="ml-auto flex h-[42px] w-[42px] items-center justify-center rounded-full bg-gradient-to-br from-brand-600 to-cyan-400 text-[11px] font-bold text-white transition-transform hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-2"
          onClick={onBackHome}
          type="button"
        >
          SP
        </button>
      </div>
    </header>
  );
}

function WorkbenchEntry({ loading, metrics, onModuleChange }) {
  return (
    <>
      <div className="mt-6">
        <WorkbenchHero loading={loading} metrics={metrics} />
      </div>
      <div className="mt-12">
        <WorkbenchModuleNav onModuleChange={onModuleChange} />
      </div>
    </>
  );
}

export default function WorkbenchPage({ onBackHome }) {
  const [activeModule, setActiveModule] = useState(null);
  const workbenchData = useWorkbenchData();
  const supportChat = useSupportChat({
    onComplete: () => {
      workbenchData.refresh();
    },
  });

  function openModule(moduleKey) {
    setActiveModule(moduleKey);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const activeMeta = activeModule ? moduleMeta[activeModule] : null;

  return (
    <div className="min-h-screen bg-page pb-12">
      <ProductNav onBackHome={onBackHome} />

      <main className="px-4 sm:px-8">
        {activeModule ? (
          <WorkbenchPanel
            activeMeta={activeMeta}
            activeModule={activeModule}
            data={workbenchData}
            onBack={() => setActiveModule(null)}
            onModuleChange={openModule}
          />
        ) : (
          <WorkbenchEntry
            loading={workbenchData.loading}
            metrics={workbenchData.metrics}
            onModuleChange={openModule}
          />
        )}

        <div className="mx-auto max-w-[1232px]">
          <DebugDrawer chat={supportChat} onRefresh={workbenchData.refresh} />
        </div>
      </main>
    </div>
  );
}
