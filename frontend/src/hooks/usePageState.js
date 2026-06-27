import { useState } from "react";

export function usePageState(initialPage = "home") {
  const [page, setPage] = useState(initialPage);

  return {
    page,
    goHome: () => setPage("home"),
    goWorkbench: () => setPage("workbench"),
    goChatDemo: () => setPage("chat-demo"),
  };
}
