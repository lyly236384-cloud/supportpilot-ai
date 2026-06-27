import { useCallback, useState } from "react";
import { sendProductChatMessage } from "../services/supportApi";

const WELCOME_MESSAGE = {
  role: "assistant",
  content: "你好，我可以介绍 SupportPilot AI 的文本 AI、知识库、转人工和数据分析能力。",
};

export function useProductChat() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const send = useCallback(async (text) => {
    const trimmed = text.trim();
    if (!trimmed || pending) return;

    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setPending(true);
    setError("");

    try {
      const { answer } = await sendProductChatMessage({ message: trimmed });
      setMessages((current) => [...current, { role: "assistant", content: answer }]);
    } catch (requestError) {
      setError(requestError.message);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: "暂时无法回答，请稍后再试。" },
      ]);
    } finally {
      setPending(false);
    }
  }, [pending]);

  return { messages, pending, error, send };
}
