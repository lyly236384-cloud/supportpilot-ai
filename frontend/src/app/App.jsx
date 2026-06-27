import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { usePageState } from "../hooks/usePageState";

const HomePage = lazy(() => import("../pages/home/HomePage"));
const WorkbenchPage = lazy(() => import("../pages/workbench/WorkbenchPage"));
const ChatDemoPage = lazy(() => import("../pages/chat-demo/ChatDemoPage"));

function PageTransition({ children, pageKey }) {
  const [visible, setVisible] = useState(false);
  const prevKey = useRef(pageKey);

  useEffect(() => {
    if (prevKey.current !== pageKey) {
      setVisible(false);
      const id = requestAnimationFrame(() => {
        requestAnimationFrame(() => setVisible(true));
      });
      prevKey.current = pageKey;
      return () => cancelAnimationFrame(id);
    }
    setVisible(true);
  }, [pageKey]);

  return (
    <div
      className="min-h-screen bg-page"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(6px)",
        transition: "opacity 0.3s ease-out, transform 0.3s ease-out",
      }}
    >
      {children}
    </div>
  );
}

export default function App() {
  const { page, goHome, goWorkbench, goChatDemo } = usePageState("home");

  return (
    <Suspense fallback={<div className="min-h-screen bg-page" />}>
      <PageTransition pageKey={page}>
        {page === "workbench" ? (
          <WorkbenchPage onBackHome={goHome} />
        ) : page === "chat-demo" ? (
          <ChatDemoPage onBackHome={goHome} />
        ) : (
          <HomePage onEnterWorkbench={goWorkbench} onEnterChatDemo={goChatDemo} />
        )}
      </PageTransition>
    </Suspense>
  );
}
