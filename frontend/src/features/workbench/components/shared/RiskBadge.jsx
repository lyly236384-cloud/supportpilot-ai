import { StatusChip } from "./StatusChip";

const riskText = {
  high: "高风险",
  medium: "中风险",
  low: "低风险",
};

export function RiskBadge({ risk, label }) {
  const tone = risk === "high" ? "danger" : risk === "medium" ? "warning" : "success";
  return <StatusChip tone={tone}>{label ?? riskText[risk] ?? risk}</StatusChip>;
}
