from __future__ import annotations

import json
import threading
import time
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from app.agent.skills import build_skill_calls
from app.agent.verifier_agent import verify_answer
from app.config.settings import use_langgraph_engine
from app.memory.context import build_memory_snapshot
from app.models.schemas import (
    Action,
    ChatResponse,
    IntentResult,
    RiskLevel,
    RiskResult,
    VerifierResult,
    WorkflowState,
    WorkflowStep,
)
from app.rag.retriever import retrieve_knowledge
from app.services.llm_client import (
    classify_intent_with_llm,
    classify_intent_with_structured_output,
    generate_answer,
    generate_answer_with_langchain,
    generate_free_chat_answer,
    get_chat_openai,
    get_llm_token_usage,
    is_llm_enabled,
    record_llm_response_usage,
    risk_check_with_llm,
    risk_check_with_structured_output,
    reset_llm_token_usage,
    stream_free_chat_answer,
)
from app.services.metrics_service import record_trace_metrics
from app.storage import repository
from app.tools.mock_tools import SUPPORT_TOOLS
from app.templates.loader import (
    get_handoff_answer,
    get_insufficient_knowledge_answer,
    get_ticket_answer,
    get_ticket_title,
    get_tool_execution_detail,
)
_trace_lock = threading.Lock()


def decide_action(
    risk: RiskResult,
    citations_count: int,
    *,
    intent: IntentResult | None = None,
    verifier_passed: bool = True,
) -> Action:
    if risk.requires_ticket:
        return Action.CREATE_TICKET
    if risk.requires_human:
        return Action.HANDOFF
    # Only handoff on zero citations when risk isn't low (e.g. greetings are fine)
    if citations_count == 0 and risk.risk_level != RiskLevel.LOW:
        return Action.HANDOFF
    if risk.risk_level == RiskLevel.HIGH:
        return Action.HANDOFF
    if intent is not None and intent.confidence < 0.6:
        return Action.HANDOFF
    if not verifier_passed:
        return Action.HANDOFF
    return Action.AUTO_REPLY


def _needs_manual_answer_path(risk: RiskResult) -> bool:
    return risk.requires_human or risk.requires_ticket or risk.risk_level == RiskLevel.HIGH


def _build_manual_answer(risk: RiskResult) -> str:
    if risk.requires_ticket:
        return get_ticket_answer()
    return get_handoff_answer()


_BUSINESS_QUESTION_MARKERS = (
    "怎么", "如何", "什么", "为什么", "能不能", "可以", "能否",
    "支持", "退款", "退货", "发货", "快递", "物流", "订单", "投诉",
    "价格", "费用", "多少钱", "在哪", "什么时候", "申请", "怎样",
)


def _looks_like_out_of_scope_question(message: str) -> bool:
    """Return True when a message looks like a substantive business question
    that the KB simply doesn't cover (not chitchat)."""
    text = message.strip()
    if len(text) < 4:
        return False
    return any(marker in text for marker in _BUSINESS_QUESTION_MARKERS)


def _is_free_chat_mode(
    intent: IntentResult,
    citations: list,
    risk: RiskResult,
    *,
    message: str = "",
) -> bool:
    """判断是否走自由对话路径（LLM 自主回答，不强制知识库引用）。"""
    from app.models.schemas import Intent

    if risk.risk_level == RiskLevel.HIGH:
        return False
    if risk.requires_ticket:
        return False
    if intent.intent != Intent.UNKNOWN:
        return False

    no_good_citations = not citations or all(c.score < 0.15 for c in citations)
    if not no_good_citations:
        return False

    # Out-of-scope business questions should be escalated, not auto-replied
    if message and _looks_like_out_of_scope_question(message):
        return False

    return True


def _resolve_answer_and_action(
    message: str,
    intent: IntentResult,
    risk: RiskResult,
    citations: list,
    *,
    use_langchain: bool = False,
    history=None,
) -> tuple[str, Action, VerifierResult]:
    # Free-chat path (checked first — overrides low-confidence handoff for chitchat)
    if _is_free_chat_mode(intent, citations, risk, message=message):
        answer = generate_free_chat_answer(message, history)
        verifier = VerifierResult(passed=True, reason="自由对话路径，已通过安全护栏")
        action = Action.AUTO_REPLY
        return answer, action, verifier

    if _needs_manual_answer_path(risk):
        answer = _build_manual_answer(risk)
        verifier = VerifierResult(passed=True, reason="人工/工单路径，跳过自动回复校验")
        action = decide_action(risk, len(citations), intent=intent, verifier_passed=True)
        return answer, action, verifier

    if use_langchain:
        answer = generate_answer_with_langchain(message, intent.intent, citations, history)
    else:
        answer = generate_answer(message, intent.intent, citations)

    verifier = verify_answer(message, answer, citations, risk, intent)
    action = decide_action(
        risk,
        len(citations),
        intent=intent,
        verifier_passed=verifier.passed,
    )
    if not verifier.passed and action == Action.AUTO_REPLY:
        action = Action.HANDOFF
        answer = get_insufficient_knowledge_answer()
    return answer, action, verifier


def _build_workflow_steps(
    intent: IntentResult,
    risk: RiskResult,
    citations_count: int,
    action: Action,
    ticket_created: bool,
    verifier: VerifierResult | None = None,
) -> list[WorkflowStep]:
    verifier_detail = verifier.reason if verifier else "未执行答复校验"
    return [
        WorkflowStep(
            name="1. 意图识别",
            status="completed",
            summary=f"识别为 {intent.intent.value}，置信度 {intent.confidence:.2f}",
            detail=intent.reason,
        ),
        WorkflowStep(
            name="2. 风险判断",
            status="completed",
            summary=f"风险等级 {risk.risk_level.value}",
            detail=risk.reason,
        ),
        WorkflowStep(
            name="3. 知识库检索",
            status="completed" if citations_count else "warning",
            summary=f"命中 {citations_count} 条知识片段",
            detail="用于约束 AI 回复，避免无依据回答" if citations_count else "未找到可靠依据，后续会转人工兜底",
        ),
        WorkflowStep(
            name="4. 动作决策",
            status="completed",
            summary=f"最终动作：{action.value}",
            detail=f"{verifier_detail}；根据风险、检索与校验结果决定自动回复、转人工或创建工单",
        ),
        WorkflowStep(
            name="5. 工具执行",
            status="completed" if ticket_created else "skipped",
            summary="已创建工单并发送通知" if ticket_created else "本轮无需调用工单工具",
            detail=get_tool_execution_detail(),
        ),
    ]

def _log_trace(response: ChatResponse) -> None:
    from datetime import datetime, timezone

    payload = json.loads(response.model_dump_json(ensure_ascii=False))
    payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    with _trace_lock:
        repository.append_trace_row(payload)
    record_trace_metrics(response.action.value, response.elapsed_ms, response.estimated_tokens)


NODE_DISPLAY: dict[str, str] = {
    "classify_intent": "1. 意图识别",
    "check_risk": "2. 风险判断",
    "retrieve_knowledge": "3. 知识库检索",
    "generate_answer": "4. 生成回复",
    "generate_free_chat_answer": "4. 生成回复",
    "prepare_manual_answer": "4. 生成回复",
    "verify_answer": "5. 答复校验",
    "decide_action": "6. 动作决策",
    "execute_tools": "7. 工具执行",
    "finalize": "8. 组装响应",
}


def node_classify_intent(state: WorkflowState) -> dict:
    result = classify_intent_with_structured_output(
        state["message"], state.get("history")
    )
    return {"intent": result}


def node_check_risk(state: WorkflowState) -> dict:
    result = risk_check_with_structured_output(state["intent"], state["message"])
    return {"risk": result}


def node_retrieve_knowledge(state: WorkflowState) -> dict:
    citations = retrieve_knowledge(state["message"], intent=state["intent"].intent)
    return {"citations": citations}


def node_generate_answer(state: WorkflowState) -> dict:
    answer = generate_answer_with_langchain(
        state["message"], state["intent"].intent, state["citations"], state.get("history")
    )
    return {"answer": answer}


def node_free_chat_answer(state: WorkflowState) -> dict:
    """Free-chat node: LLM autonomous dialogue, no RAG citations required."""
    answer = generate_free_chat_answer(state["message"], state.get("history"))
    return {"answer": answer, "citations": []}


def node_prepare_manual_answer(state: WorkflowState) -> dict:
    answer = _build_manual_answer(state["risk"])
    verifier = VerifierResult(passed=True, reason="人工/工单路径，跳过自动回复校验")
    action = decide_action(
        state["risk"],
        len(state["citations"]),
        intent=state["intent"],
        verifier_passed=True,
    )
    return {"answer": answer, "verifier": verifier, "action": action}


def node_verify_answer(state: WorkflowState) -> dict:
    free_chat = _is_free_chat_mode(
        state["intent"], state["citations"], state["risk"], message=state["message"]
    )
    verifier = verify_answer(
        state["message"],
        state["answer"],
        state["citations"],
        state["risk"],
        state["intent"],
        is_free_chat=free_chat,
    )
    action = decide_action(
        state["risk"],
        len(state["citations"]),
        intent=state["intent"],
        verifier_passed=verifier.passed,
    )
    answer = state["answer"]
    if not verifier.passed and action == Action.AUTO_REPLY:
        action = Action.HANDOFF
        answer = get_insufficient_knowledge_answer()
    return {"verifier": verifier, "action": action, "answer": answer}


def node_decide_action(state: WorkflowState) -> dict:
    action = decide_action(state["risk"], len(state["citations"]), intent=state["intent"])
    return {"action": action}


def node_execute_tools(state: WorkflowState) -> dict:
    customer, ticket, notification = _execute_ticket_tools(
        state["customer_id"], state["message"]
    )
    return {"customer": customer, "ticket": ticket, "notification": notification}


def node_finalize(state: WorkflowState) -> dict:
    elapsed_ms = int((time.perf_counter() - state["start_time"]) * 1000)
    ticket_created = state.get("ticket") is not None
    skill_calls = build_skill_calls(
        state["intent"],
        state["risk"],
        len(state["citations"]),
        state["action"],
        ticket_created,
    )
    memory_snapshot = build_memory_snapshot(
        state["customer_id"],
        state["message"],
        state["intent"],
        state["risk"],
        state["action"],
        state["citations"],
    )
    steps = _build_workflow_steps(
        state["intent"],
        state["risk"],
        len(state["citations"]),
        state["action"],
        ticket_created,
        state.get("verifier"),
    )
    return {
        "workflow_steps": steps,
        "skill_calls": skill_calls,
        "memory_snapshot": memory_snapshot,
        "elapsed_ms": elapsed_ms,
        "llm_token_usage": get_llm_token_usage(),
    }


# -----------------------------------------------------------
#  Conditional routing
# -----------------------------------------------------------


def route_after_retrieve(state: WorkflowState) -> str:
    # Free-chat checked first: low-confidence UNKNOWN + no citations should
    # enter LLM autonomous dialogue rather than being handed off to human.
    if _is_free_chat_mode(
        state["intent"], state["citations"], state["risk"], message=state["message"]
    ):
        return "generate_free_chat_answer"
    if _needs_manual_answer_path(state["risk"]):
        return "prepare_manual_answer"
    return "generate_answer"


def route_after_decision(state: WorkflowState) -> str:
    if state["action"] == Action.CREATE_TICKET:
        return "execute_tools"
    return "finalize"


# -----------------------------------------------------------
#  Graph builder
# -----------------------------------------------------------


def build_langgraph_workflow() -> StateGraph:
    builder = StateGraph(WorkflowState)

    builder.add_node("classify_intent", node_classify_intent)
    builder.add_node("check_risk", node_check_risk)
    builder.add_node("retrieve_knowledge", node_retrieve_knowledge)
    builder.add_node("generate_answer", node_generate_answer)
    builder.add_node("generate_free_chat_answer", node_free_chat_answer)
    builder.add_node("prepare_manual_answer", node_prepare_manual_answer)
    builder.add_node("verify_answer", node_verify_answer)
    builder.add_node("execute_tools", node_execute_tools)
    builder.add_node("finalize", node_finalize)

    builder.add_edge(START, "classify_intent")
    builder.add_edge("classify_intent", "check_risk")
    builder.add_edge("check_risk", "retrieve_knowledge")
    builder.add_conditional_edges(
        "retrieve_knowledge",
        route_after_retrieve,
        {
            "prepare_manual_answer": "prepare_manual_answer",
            "generate_answer": "generate_answer",
            "generate_free_chat_answer": "generate_free_chat_answer",
        },
    )
    builder.add_edge("generate_answer", "verify_answer")
    builder.add_edge("generate_free_chat_answer", "verify_answer")
    builder.add_conditional_edges(
        "verify_answer",
        route_after_decision,
        {"execute_tools": "execute_tools", "finalize": "finalize"},
    )
    builder.add_conditional_edges(
        "prepare_manual_answer",
        route_after_decision,
        {"execute_tools": "execute_tools", "finalize": "finalize"},
    )
    builder.add_edge("execute_tools", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()


# -----------------------------------------------------------
#  Sync entry point (used by POST /api/chat)
# -----------------------------------------------------------


def _run_langgraph_sync(customer_id: str, message: str, history=None) -> ChatResponse:
    reset_llm_token_usage()
    graph = build_langgraph_workflow()
    trace_id = f"trace_{uuid4().hex[:10]}"

    input_state: WorkflowState = {
        "customer_id": customer_id,
        "message": message,
        "trace_id": trace_id,
        "history": history or [],
        "citations": [],
        "workflow_steps": [],
        "start_time": time.perf_counter(),
    }

    final_state = graph.invoke(input_state)
    response = _chat_response_from_state(final_state, trace_id, customer_id, message)
    _log_trace(response)
    return response


def _chat_response_from_state(
    final_state: WorkflowState,
    trace_id: str,
    customer_id: str,
    message: str,
) -> ChatResponse:
    verifier = final_state.get("verifier")
    return ChatResponse(
        trace_id=trace_id,
        customer_id=customer_id,
        message=message,
        intent=final_state["intent"],
        risk=final_state["risk"],
        action=final_state["action"],
        answer=final_state["answer"],
        citations=final_state["citations"],
        workflow_steps=final_state["workflow_steps"],
        ticket=final_state.get("ticket"),
        notification=final_state.get("notification"),
        elapsed_ms=final_state["elapsed_ms"],
        estimated_tokens=final_state.get("llm_token_usage", get_llm_token_usage()),
        skill_calls=final_state.get("skill_calls", []),
        memory_snapshot=final_state.get("memory_snapshot"),
        verifier_passed=verifier.passed if verifier else None,
        verifier_reason=verifier.reason if verifier else "",
    )


# -----------------------------------------------------------
#  Async streaming entry point (used by POST /api/chat/stream)
# -----------------------------------------------------------


async def run_langgraph_stream(customer_id: str, message: str, history=None):
    """Async generator yielding LangGraph node events for SSE streaming."""
    reset_llm_token_usage()
    graph = build_langgraph_workflow()
    trace_id = f"trace_{uuid4().hex[:10]}"

    input_state: WorkflowState = {
        "customer_id": customer_id,
        "message": message,
        "trace_id": trace_id,
        "history": history or [],
        "citations": [],
        "workflow_steps": [],
        "start_time": time.perf_counter(),
    }

    final_state = None
    async for event in graph.astream_events(input_state, version="v2"):
        kind = event["event"]
        name = event.get("name", "")

        if kind == "on_chain_start" and name in NODE_DISPLAY:
            yield {
                "type": "step_start",
                "step": name,
                "display": NODE_DISPLAY[name],
            }
        elif kind == "on_chain_end" and name in NODE_DISPLAY:
            output = event["data"].get("output", {})
            yield {
                "type": "step_complete",
                "step": name,
                "display": NODE_DISPLAY[name],
                "output": _serialize_step_output(name, output),
            }
        elif kind == "on_chain_end" and name == "LangGraph":
            final_state = event["data"].get("output")

    # After the graph completes, build and yield the final ChatResponse.
    if final_state is not None:
        response = _chat_response_from_state(final_state, trace_id, customer_id, message)
        _log_trace(response)
        yield {
            "type": "final",
            "response": response.model_dump(mode="json"),
        }


async def run_procedural_stream(customer_id: str, message: str, history=None):
    reset_llm_token_usage()
    trace_id = f"trace_{uuid4().hex[:10]}"
    start = time.perf_counter()

    yield {"type": "step_start", "step": "classify_intent", "display": NODE_DISPLAY["classify_intent"]}
    intent = classify_intent_with_llm(message, history)
    yield {
        "type": "step_complete",
        "step": "classify_intent",
        "display": NODE_DISPLAY["classify_intent"],
        "output": _serialize_step_output("classify_intent", {"intent": intent}),
    }

    yield {"type": "step_start", "step": "check_risk", "display": NODE_DISPLAY["check_risk"]}
    risk = risk_check_with_llm(intent, message)
    yield {
        "type": "step_complete",
        "step": "check_risk",
        "display": NODE_DISPLAY["check_risk"],
        "output": _serialize_step_output("check_risk", {"risk": risk}),
    }

    yield {"type": "step_start", "step": "retrieve_knowledge", "display": NODE_DISPLAY["retrieve_knowledge"]}
    citations = retrieve_knowledge(message, intent=intent.intent)
    yield {
        "type": "step_complete",
        "step": "retrieve_knowledge",
        "display": NODE_DISPLAY["retrieve_knowledge"],
        "output": _serialize_step_output("retrieve_knowledge", {"citations": citations}),
    }

    free_chat = _is_free_chat_mode(intent, citations, risk, message=message)
    answer_step = (
        "generate_free_chat_answer" if free_chat
        else "prepare_manual_answer" if _needs_manual_answer_path(risk)
        else "generate_answer"
    )
    yield {"type": "step_start", "step": answer_step, "display": NODE_DISPLAY[answer_step]}

    if free_chat:
        # --- 两阶段流式自由对话：思考 → 回答 ---
        answer_parts: list[str] = []
        async for item in stream_free_chat_answer(message, history):
            if item[0] == "thinking":
                yield {"type": "thinking", "step": answer_step, "content": item[1]}
            else:
                answer_parts.append(item[1])
                yield {"type": "token", "step": answer_step, "token": item[1]}
        answer = "".join(answer_parts)
        verifier = VerifierResult(passed=True, reason="自由对话路径，已通过安全护栏")
        action = Action.AUTO_REPLY
    else:
        answer, action, verifier = _resolve_answer_and_action(
            message, intent, risk, citations, use_langchain=True, history=history
        )

    yield {
        "type": "step_complete",
        "step": answer_step,
        "display": NODE_DISPLAY[answer_step],
        "output": {"summary": "回复已生成"},
    }

    if not _needs_manual_answer_path(risk):
        yield {"type": "step_start", "step": "verify_answer", "display": NODE_DISPLAY["verify_answer"]}
        yield {
            "type": "step_complete",
            "step": "verify_answer",
            "display": NODE_DISPLAY["verify_answer"],
            "output": _serialize_step_output("verify_answer", {"verifier": verifier, "action": action}),
        }

    ticket, notification = None, None
    if action == Action.CREATE_TICKET:
        yield {"type": "step_start", "step": "execute_tools", "display": NODE_DISPLAY["execute_tools"]}
        _, ticket, notification = _execute_ticket_tools(customer_id, message)
        yield {
            "type": "step_complete",
            "step": "execute_tools",
            "display": NODE_DISPLAY["execute_tools"],
            "output": _serialize_step_output("execute_tools", {"ticket": ticket}),
        }

    response = _assemble_chat_response(
        trace_id, customer_id, message, intent, risk, action,
        answer, citations, ticket, notification, start, verifier,
    )
    _log_trace(response)
    yield {"type": "final", "response": response.model_dump(mode="json")}


async def run_support_stream(customer_id: str, message: str, history=None):
    if use_langgraph_engine():
        async for event in run_langgraph_stream(customer_id, message, history):
            yield event
        return

    async for event in run_procedural_stream(customer_id, message, history):
        yield event


def _serialize_step_output(node_name: str, output: dict) -> dict:
    """Extract a human-readable summary from a node's state update."""
    if node_name == "classify_intent" and "intent" in output:
        intent = output["intent"]
        return {
            "summary": f"识别为 {intent.intent.value}，置信度 {intent.confidence:.2f}",
            "detail": intent.reason,
        }
    if node_name == "check_risk" and "risk" in output:
        risk = output["risk"]
        return {
            "summary": f"风险等级 {risk.risk_level.value}",
            "detail": risk.reason,
        }
    if node_name == "retrieve_knowledge" and "citations" in output:
        count = len(output["citations"])
        return {
            "summary": f"命中 {count} 条知识片段",
            "detail": "用于约束 AI 回复" if count else "未找到可靠依据",
        }
    if node_name == "generate_answer":
        return {"summary": "回复已生成"}
    if node_name == "prepare_manual_answer":
        return {"summary": "已生成人工接管说明"}
    if node_name == "verify_answer" and "verifier" in output:
        verifier = output["verifier"]
        return {
            "summary": "通过" if verifier.passed else "未通过",
            "detail": verifier.reason,
        }
    if node_name == "decide_action" and "action" in output:
        return {"summary": f"最终动作：{output['action'].value}"}
    if node_name == "execute_tools":
        return {"summary": "已创建工单并发送通知" if output.get("ticket") else "无需执行工具"}
    if node_name == "finalize":
        return {"summary": "工作流完成"}
    return {}


def _assemble_chat_response(
    trace_id: str,
    customer_id: str,
    message: str,
    intent: IntentResult,
    risk: RiskResult,
    action: Action,
    answer: str,
    citations: list,
    ticket,
    notification,
    start_time: float,
    verifier: VerifierResult,
) -> ChatResponse:
    """Build a ChatResponse from discrete workflow outputs.

    Shared by the procedural sync path and the procedural streaming path to avoid
    duplicating the telemetry, skill-call, and memory-snapshot wiring.
    """
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    estimated_tokens = get_llm_token_usage()
    ticket_created = ticket is not None
    workflow_steps = _build_workflow_steps(
        intent, risk, len(citations), action, ticket_created, verifier
    )
    skill_calls = build_skill_calls(
        intent, risk, len(citations), action, ticket_created
    )
    memory_snapshot = build_memory_snapshot(
        customer_id, message, intent, risk, action, citations
    )
    return ChatResponse(
        trace_id=trace_id,
        customer_id=customer_id,
        message=message,
        intent=intent,
        risk=risk,
        action=action,
        answer=answer,
        citations=citations,
        workflow_steps=workflow_steps,
        ticket=ticket,
        notification=notification,
        elapsed_ms=elapsed_ms,
        estimated_tokens=estimated_tokens,
        skill_calls=skill_calls,
        memory_snapshot=memory_snapshot,
        verifier_passed=verifier.passed,
        verifier_reason=verifier.reason,
    )


def _execute_ticket_tools(customer_id: str, message: str):
    """Run the ticket path through LLM function-calling, with deterministic fallback."""
    if is_llm_enabled():
        try:
            result = _execute_ticket_tools_with_llm(customer_id, message)
            if result is not None:
                return result
        except Exception:
            pass
    return _execute_ticket_tools_deterministic(customer_id, message)


def _execute_ticket_tools_deterministic(customer_id: str, message: str):
    """Run the registered LangChain tools directly when the LLM is unavailable."""
    tool_by_name = {tool.name: tool for tool in SUPPORT_TOOLS}

    customer = tool_by_name["get_customer_profile_tool"].invoke(
        {"customer_id": customer_id}
    )
    priority = "P0" if customer.get("is_vip") else "P1"
    ticket = tool_by_name["create_ticket_tool"].invoke(
        {
            "customer_id": customer_id,
            "title": get_ticket_title(),
            "summary": message,
            "priority": priority,
        }
    )
    notification = tool_by_name["send_alert_tool"].invoke(
        {"ticket": ticket, "customer": customer}
    )
    return customer, ticket, notification


def _execute_ticket_tools_with_llm(customer_id: str, message: str):
    llm = get_chat_openai(temperature=0.0)
    if llm is None:
        return None

    tool_by_name = {tool.name: tool for tool in SUPPORT_TOOLS}
    llm_with_tools = llm.bind_tools(SUPPORT_TOOLS)
    messages = [
        SystemMessage(
            content=(
                "You are a support operations agent. Use tools to handle a "
                "ticket-worthy customer issue. First fetch the customer profile, "
                "then create a ticket with priority P0 for VIP customers and P1 "
                "otherwise, then send an alert. Do not invent tool results."
            )
        ),
        HumanMessage(
            content=(
                f"customer_id={customer_id}\n"
                f"ticket_title={get_ticket_title()}\n"
                f"customer_message={message}"
            )
        ),
    ]

    customer = None
    ticket = None
    notification = None

    for _ in range(4):
        response = llm_with_tools.invoke(messages)
        record_llm_response_usage(response)
        messages.append(response)
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            break

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool = tool_by_name.get(tool_name)
            if tool is None:
                continue
            output = tool.invoke(tool_call.get("args") or {})
            if tool_name == "get_customer_profile_tool":
                customer = output
            elif tool_name == "create_ticket_tool":
                ticket = output
            elif tool_name == "send_alert_tool":
                notification = output
            messages.append(
                ToolMessage(
                    content=_tool_message_content(output),
                    tool_call_id=tool_call["id"],
                )
            )

        if customer is not None and ticket is not None and notification is not None:
            return customer, ticket, notification

    return None


def _tool_message_content(value) -> str:
    if hasattr(value, "model_dump"):
        return value.model_dump_json()
    return json.dumps(value, ensure_ascii=False, default=str)


def run_support_workflow(customer_id: str, message: str, history=None) -> ChatResponse:
    reset_llm_token_usage()
    if use_langgraph_engine():
        return _run_langgraph_sync(customer_id, message, history)

    start = time.perf_counter()
    trace_id = f"trace_{uuid4().hex[:10]}"

    intent = classify_intent_with_llm(message, history)
    risk = risk_check_with_llm(intent, message)
    citations = retrieve_knowledge(message, intent=intent.intent)
    answer, action, verifier = _resolve_answer_and_action(
        message, intent, risk, citations, use_langchain=True, history=history
    )

    ticket, notification = None, None
    if action == Action.CREATE_TICKET:
        _, ticket, notification = _execute_ticket_tools(customer_id, message)

    response = _assemble_chat_response(
        trace_id, customer_id, message, intent, risk, action,
        answer, citations, ticket, notification, start, verifier,
    )
    _log_trace(response)
    return response
