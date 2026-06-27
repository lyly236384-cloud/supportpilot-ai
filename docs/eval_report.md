# Eval Report

这份报告说明 SupportPilot AI 如何用 eval 验证工作流、规则兜底和真实 LLM 的取舍。

## 目标

客服 Agent 的评估不能只看“回答是否自然”，还要看：

- 意图是否识别正确
- 动作是否决策正确
- 高风险请求是否安全升级
- RAG 是否命中知识库
- 规则与 LLM 的边界在哪里

因此项目维护了一套轻量 eval，用固定用例对 mock 规则引擎和真实 LLM 进行对比。

## 用例分类

评估集位于：

```text
backend/scripts/eval_cases.json
```

共覆盖 7 类输入：

| 类别 | 目标 |
|---|---|
| clear | 清晰、直接的业务问题 |
| paraphrase | 同义改写，测试规则泛化能力 |
| implicit | 隐含意图，测试上下文理解 |
| ambiguous | 模糊表达，测试 LLM 语义判断 |
| out_of_scope | 非业务问题，测试安全降级 |
| adversarial | 越权/提示注入，测试护栏 |
| greeting | 问候语，测试短路路径 |

## 指标

`run_eval.py` 输出以下指标：

- `intent_accuracy`：意图识别准确率
- `action_accuracy`：动作决策准确率
- `end_to_end_accuracy`：意图与动作同时正确的比例
- `rag_hit_rate`：RAG 是否命中知识片段
- `safety_escalation_rate`：高风险/对抗用例是否正确转人工
- `category_accuracy`：分类型准确率
- `intent_confusion`：意图混淆情况

## 规则引擎 vs 真实 LLM

同一 20 条用例上，规则引擎与真实 LLM 的对比结论：

| 指标 | 规则引擎 | 真实 LLM |
|---|---:|---:|
| 端到端准确率 | 75% | 受动作决策波动影响 |
| 意图准确率 | 75% | 90% |
| 安全升级率 | 100% | 100% |
| implicit 隐含意图 | 0% | 100% |
| ambiguous 模糊表达 | 0% | 100% |
| paraphrase 同义改写 | 0% | 50% |

## 结论

1. LLM 明显提升语义泛化能力  
   在隐含意图、模糊表达、改写表达上，关键词规则容易失效，而真实 LLM 能更好理解用户语义。

2. 高风险路径必须保留规则兜底  
   投诉、赔偿、隐私、提示注入等场景要求确定性和可解释性。即使 LLM 泛化更强，高风险动作也不应完全依赖模型自由判断。

3. eval 支撑混合架构设计  
   项目最终采用“高风险规则兜底 + 常规路径 LLM 泛化”的混合决策，而不是全规则或全 LLM。

4. 测试保证工程稳定性  
   89 个单元测试覆盖 API、工作流、RAG 检索、风险判断、工具调用、结构化输出兜底等核心路径，本机完整环境 100% 通过；其中 2 个 dense 向量检索测试在缺少离线 embedding 模型的环境会通过 `importorskip` 自动跳过，此时为 `87 passed, 2 skipped`，业务逻辑测试不受影响。

## 如何运行

默认规则引擎 eval：

```powershell
cd SupportPilot-AI-MVP\backend
python scripts\run_eval.py
```

真实 LLM 对比：

```powershell
cd SupportPilot-AI-MVP\backend
$env:LLM_PROVIDER = "deepseek"
$env:DEEPSEEK_API_KEY = "<your-key>"
python scripts\run_eval_compare.py
```

单元测试：

```powershell
cd SupportPilot-AI-MVP\backend
python -m pytest -q
```
