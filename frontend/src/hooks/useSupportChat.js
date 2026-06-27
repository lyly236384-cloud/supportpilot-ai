import { useCallback, useRef, useState } from "react";
import { requestChatStream } from "../services/apiClient";

// Default demo_ecommerce examples: industry sample data, not platform-only behavior.
const DEMO_CASES = [
  { customerId: "shop_001", message: "我的快递什么时候发货？" },
  { customerId: "shop_002", message: "订单已经发货了，还能修改收货地址吗？" },
  { customerId: "shop_003", message: "我想退货，七天无理由怎么申请？" },
  { customerId: "shop_001", message: "收到的杯子碎了，外包装也变形了" },
  { customerId: "shop_003", message: "我要投诉你们并要求赔偿" },
];

export function useSupportChat({ onComplete, onToken, onThinking } = {}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [steps, setSteps] = useState([]);
  const [streamEvents, setStreamEvents] = useState([]);
  const [result, setResult] = useState(null);
  const [streamingText, setStreamingText] = useState("");
  const [thinking, setThinking] = useState(false);
  const [thinkingContent, setThinkingContent] = useState("");

  // Use refs to always access the latest callbacks without re-creating run
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;
  const onTokenRef = useRef(onToken);
  onTokenRef.current = onToken;
  const onThinkingRef = useRef(onThinking);
  onThinkingRef.current = onThinking;

  const reset = useCallback(() => {
    setError("");
    setSteps([]);
    setStreamEvents([]);
    setResult(null);
    setStreamingText("");
    setThinking(false);
    setThinkingContent("");
  }, []);

  const run = useCallback(async ({ customerId, message, history = [] }) => {
    if (!message.trim()) return;

    setPending(true);
    setError("");
    setSteps([]);
    setStreamEvents([]);
    setResult(null);
    setStreamingText("");
    setThinking(false);
    setThinkingContent("");

    const streamStartedAt = performance.now();

    try {
      await requestChatStream(
        { customer_id: customerId, message, history },
        (event) => {
        const envelope = {
          ...event,
          receivedAt: performance.now() - streamStartedAt,
        };
        setStreamEvents((current) => [...current, envelope]);

        if (event.type === "thinking") {
          setThinking(true);
          setThinkingContent(event.content ?? "");
          onThinkingRef.current?.(event.content ?? true);
        }

        if (event.type === "token") {
          setThinking(false);
          const token = event.token ?? "";
          setStreamingText((current) => current + token);
          onTokenRef.current?.(token);
        }

        if (event.type === "step_start") {
          setSteps((current) => [
            ...current,
            {
              name: event.display ?? event.step,
              status: "running",
              summary: "执行中…",
              detail: "",
            },
          ]);
        }

        if (event.type === "step_complete") {
          setSteps((current) => {
            const next = [...current];
            const index = next.findIndex((step) => step.name === (event.display ?? event.step));
            const output = event.output ?? {};
            const updated = {
              name: event.display ?? event.step,
              status: "completed",
              summary: output.summary ?? "已完成",
              detail: typeof output.detail === "string" ? output.detail : "",
            };

            if (index >= 0) {
              next[index] = updated;
              return next;
            }

            return [...next, updated];
          });
        }

        if (event.type === "final") {
          const response = event.response ?? null;
          setResult(response);
          setStreamingText("");
          setThinking(false);
          setThinkingContent("");
          if (response?.workflow_steps?.length) {
            setSteps(response.workflow_steps);
          }
          // Use ref to always call the latest onComplete
          onCompleteRef.current?.(response);
        }
      },
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setPending(false);
    }
  }, []);  // empty deps — stable reference, uses ref for onComplete

  return {
    demoCases: DEMO_CASES,
    pending,
    error,
    steps,
    streamEvents,
    result,
    streamingText,
    thinking,
    thinkingContent,
    run,
    reset,
  };
}
