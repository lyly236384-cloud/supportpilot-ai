import { useEffect, useRef, useState } from "react";
import { fetchCustomers } from "../../services/supportApi";
import { useSupportChat } from "../../hooks/useSupportChat";
import { ChatBubble } from "./ChatBubble";
import { ChatDemoNav } from "./ChatDemoNav";
import { ChatInput } from "./ChatInput";
import { CustomerSelector } from "./CustomerSelector";

function formatTime() {
  return new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function EmptyChat() {
  return (
    <div className="flex flex-1 items-center justify-center px-4">
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-brand-50">
          <svg className="h-8 w-8 text-brand-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
            <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h3 className="mt-4 text-sm font-semibold text-slate-600">选择一位模拟客户，开始体验 AI 客服对话</h3>
        <p className="mt-2 text-sm text-slate-400">点击上方快捷案例或输入您的问题</p>
      </div>
    </div>
  );
}

function ThinkingBubble({ content }) {
  return (
    <div className="flex gap-3 animate-fade-in-up">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-amber-600 text-white">
        <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <div className="max-w-[85%] rounded-2xl border border-amber-200 bg-amber-50/70 px-4 py-2.5 shadow-sm">
        <p className="text-[11px] font-semibold text-amber-600 tracking-wide mb-1">AI 正在思考⋯</p>
        <p className="text-xs text-slate-600 leading-relaxed">{content}</p>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-[11px] font-semibold text-white">
        AI
      </div>
      <div className="flex items-center gap-1 rounded-2xl border border-line bg-white px-5 py-3">
        <span className="h-2 w-2 animate-pulse rounded-full bg-brand-400" style={{ animationDelay: "0ms" }} />
        <span className="h-2 w-2 animate-pulse rounded-full bg-brand-400" style={{ animationDelay: "200ms" }} />
        <span className="h-2 w-2 animate-pulse rounded-full bg-brand-400" style={{ animationDelay: "400ms" }} />
        <span className="ml-1 text-xs text-slate-400">AI 客服正在输入…</span>
      </div>
    </div>
  );
}

export default function ChatDemoPage({ onBackHome }) {
  const [customers, setCustomers] = useState([]);
  const [customersLoading, setCustomersLoading] = useState(true);
  const [customersError, setCustomersError] = useState("");
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [messages, setMessages] = useState([]);

  const listRef = useRef(null);
  const bottomRef = useRef(null);
  const userScrolledUp = useRef(false);

  const supportChat = useSupportChat({
    onComplete(response) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response?.answer ?? "系统未能生成回复，请稍后重试。",
          citations: response?.citations ?? [],
          timestamp: formatTime(),
        },
      ]);
    },
  });

  // Load customers on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      setCustomersLoading(true);
      setCustomersError("");
      try {
        const data = await fetchCustomers();
        if (!cancelled) {
          setCustomers(data ?? []);
          if (data?.length) {
            setSelectedCustomerId((prev) => prev || data[0].customer_id);
          }
        }
      } catch (err) {
        if (!cancelled) setCustomersError(err.message);
      } finally {
        if (!cancelled) setCustomersLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // Auto-scroll to bottom when messages change or pending starts
  useEffect(() => {
    if (!userScrolledUp.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, supportChat.pending, supportChat.streamingText]);

  function handleScroll() {
    const el = listRef.current;
    if (!el) return;
    const threshold = 80;
    userScrolledUp.current = el.scrollTop + el.clientHeight < el.scrollHeight - threshold;
  }

  function handleSend(message) {
    if (!message.trim() || !selectedCustomerId) return;
    // Snapshot prior turns as multi-turn history before appending the new one.
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [
      ...prev,
      { role: "user", content: message, timestamp: formatTime() },
    ]);
    userScrolledUp.current = false;
    supportChat.run({ customerId: selectedCustomerId, message, history });
  }

  function handleDemoSelect(demo) {
    if (demo.customerId) {
      setSelectedCustomerId(demo.customerId);
    }
    handleSend(demo.message);
  }

  const selectedCustomer = customers.find((c) => c.customer_id === selectedCustomerId);

  return (
    <div className="flex h-screen flex-col bg-page">
      <ChatDemoNav onBackHome={onBackHome} />
      <CustomerSelector
        customers={customers}
        loading={customersLoading}
        onChange={setSelectedCustomerId}
        selectedId={selectedCustomerId}
      />

      {customersError ? (
        <div className="mx-4 mt-2 rounded-xl bg-danger-light px-4 py-2 text-sm text-danger">
          ⚠ 加载客户列表失败：{customersError}
        </div>
      ) : null}

      <div
        className="relative flex-1 overflow-y-auto px-4 py-6"
        onScroll={handleScroll}
        ref={listRef}
      >
        {!messages.length ? (
          <EmptyChat />
        ) : (
          <div className="mx-auto flex max-w-[720px] flex-col gap-4">
            {messages.map((msg, i) => (
              <ChatBubble
                citations={msg.citations}
                content={msg.content}
                key={i}
                role={msg.role}
                timestamp={msg.timestamp}
              />
            ))}
            {supportChat.thinkingContent ? (
              <ThinkingBubble content={supportChat.thinkingContent} />
            ) : null}
            {supportChat.streamingText ? (
              <ChatBubble
                content={supportChat.streamingText}
                role="assistant"
                streaming
                timestamp={formatTime()}
              />
            ) : supportChat.pending && !supportChat.thinkingContent ? (
              <TypingIndicator />
            ) : null}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {supportChat.error ? (
        <div className="mx-4 mb-1 rounded-xl bg-danger-light px-4 py-2 text-center text-sm text-danger">
          ⚠ {supportChat.error}
        </div>
      ) : null}

      <ChatInput
        demoCases={supportChat.demoCases}
        onDemoSelect={handleDemoSelect}
        onSend={handleSend}
        pending={supportChat.pending}
      />
    </div>
  );
}
