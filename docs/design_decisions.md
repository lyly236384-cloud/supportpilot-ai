# Design Decisions

这份文档用于解释 SupportPilot AI 的关键设计取舍，重点回答面试中最容易被追问的几个问题。

## 1. 为什么不是普通 Chatbot？

客服场景不只需要“回答问题”，还需要判断风险、检索依据、决定动作、创建工单、记录处理过程。

因此项目没有把 LLM 直接接到聊天框，而是把用户消息放进一个客服运营工作流：

```text
意图识别 -> 风险判断 -> 知识库检索 -> 回答生成 -> 回答校验 -> 动作决策 -> 工具执行/人工兜底
```

这样系统具备三个能力：

- 可运营：每次对话都有动作结果，如自动回复、转人工、创建工单。
- 可观测：每次执行都有 trace、耗时、token usage 和引用来源。
- 可评估：可以用 eval 用例验证意图、动作、安全兜底和 RAG 命中。

## 2. 为什么使用 LangGraph？

客服工作流天然是多节点、带状态、带条件路由的流程。

LangGraph 的 `StateGraph` 适合表达这类流程：

- 每个节点只负责一个明确职责，例如 intent、risk、retrieve、generate、verify、tools。
- 状态在节点间显式传递，便于调试和追踪。
- `conditional_edges` 能清晰表达不同业务路径。
- `astream_events` 支持流式暴露节点执行过程，适合前端展示 AI 工作流进度。

相比把所有逻辑堆在一个函数里，LangGraph 更适合后续扩展新的节点、工具和行业模板。

## 3. 为什么保留 procedural / langgraph 双引擎？

项目同时保留 procedural 和 LangGraph 两条执行路径。

procedural 用于调试和回归，LangGraph 用于流程可视化和后续扩展，二者复用同一组节点逻辑：

- procedural 路径更直接，适合本地调试、单步排查和稳定回归。
- LangGraph 路径更适合展示工作流、条件路由和后续节点扩展。
- 两条路径复用同一组业务节点和判断逻辑，避免重复实现。

在作品集阶段，这个设计也能展示一个工程取舍：先保留可调试性，再逐步引入图式编排能力。

## 4. 为什么高风险路径不用纯 LLM？

真实客服场景里，高风险请求不能完全交给 LLM 决策。

原因有三点：

- LLM 对主观动作决策可能有非确定性波动。
- 投诉、赔偿、提示注入等场景误放行的代价高。
- 规则在高风险关键词和安全边界上更稳定、可解释、可复现。

因此项目采用混合决策：

- 高风险路径：规则优先兜底，确保安全升级率。
- 常规咨询路径：使用 LLM 提升改写表达、隐含意图和模糊表达的泛化能力。

eval 结果也支持这个取舍：真实 LLM 在 implicit / ambiguous 场景中明显优于规则，但安全升级率仍需要保持 100%。

## 5. 为什么做 Function Calling 工具闭环？

如果系统只能回答问题，它仍然更像 Chatbot。

客服 Agent 需要能“办事”，例如查询客户、创建工单、发送通知。因此项目实现了 function-calling 工具闭环：

```text
LLM -> tool_calls -> Tool Executor -> ToolMessage -> LLM
```

关键设计：

- 使用 `bind_tools` 暴露客服工具。
- 解析多轮 `tool_calls` 并执行对应工具。
- 用 `ToolMessage` 将工具结果回填给模型。
- 设置最大轮次，避免工具调用失控。
- 如果 LLM 工具路径失败，回退到确定性工具执行。

这个设计让项目从“工作流系统”进一步具备 Agentic 行为。

## 6. 为什么统计真实 token usage？

中小企业落地 AI 应用时非常关注 API 成本。

如果 token 用量只是按文本长度估算，就无法真正分析成本，也容易在面试中被追问。项目因此改为从 LLM response 的 usage 元数据读取真实 token：

- 普通 LLM 调用：读取 `usage_metadata` / `response_metadata.token_usage`。
- structured output：使用 `include_raw=True` 保留 raw response 并记录 usage。
- streaming：从 chunk 中累加 usage。
- tool calling：记录每轮 LLM tool response 的 usage。

实现上用 `ContextVar` 维护单次 workflow 的 token usage，避免在每层函数之间手动传参，同时适配异步和流式场景。

## 7. structured output 为什么要处理 parsed=None？

LangChain 在 `include_raw=True` 时，如果结构化输出解析失败，可能返回：

```python
{"raw": ..., "parsed": None, "parsing_error": ...}
```

如果直接返回 `parsed`，下游访问 `intent.intent` 或 `risk.risk_level` 会出现隐蔽错误。

项目中统一通过 helper 处理结构化结果：

- 先记录 raw response 的 token usage。
- 如果 `parsed is None`，主动抛错。
- 触发现有 fallback，回到规则分类或规则风险判断。

这样既保留了 token 可观测性，又避免结构化输出失败污染主流程。
