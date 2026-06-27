import { KnowledgePanel } from "./modules/KnowledgePanel";
import { OverviewPanel } from "./modules/OverviewPanel";
import { QueuePanel } from "./modules/QueuePanel";
import { RecordsPanel } from "./modules/RecordsPanel";
import { TicketsPanel } from "./modules/TicketsPanel";
import { EmptyState } from "./shared/EmptyState";

export function WorkbenchBody({ activeModule, data }) {
  if (data.loading) {
    return (
      <div className="mt-9">
        <EmptyState title="正在加载运营数据" desc="正在读取指标、队列、工单和知识库文档。" />
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="mt-9">
        <EmptyState title="无法读取后端数据" desc={data.error} />
      </div>
    );
  }

  if (activeModule === "overview") return <OverviewPanel data={data} />;
  if (activeModule === "queue") return <QueuePanel data={data} />;
  if (activeModule === "records") return <RecordsPanel data={data} />;
  if (activeModule === "tickets") return <TicketsPanel data={data} />;
  if (activeModule === "knowledge") return <KnowledgePanel data={data} />;

  return null;
}
