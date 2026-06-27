import { useEffect, useMemo, useState } from "react";
import { StatusChip } from "../shared/StatusChip";
import { displayMetric, formatRate } from "../shared/formatters";
import {
  DEFAULT_PAGE_SIZE,
  previousPageOffset,
  shouldReloadPreviousPage,
} from "../../utils/paginationHelpers";

const columns = [
  { title: "新建", tone: "info", match: ["Open"] },
  { title: "处理中", tone: "warning", match: ["In Progress"] },
  { title: "待客户确认", tone: "neutral", match: ["Pending", "Waiting", "Pending Customer"] },
  { title: "已完成", tone: "success", match: ["Resolved", "Closed"] },
];

function TicketCard({ ticket, selected, onSelect }) {
  if (!ticket) {
    return (
      <div className="min-h-[108px] rounded-2.5xl border border-dashed border-line bg-page px-4 py-4 text-sm text-muted">
        暂无工单
      </div>
    );
  }

  return (
    <button
      className={`min-h-[108px] w-full rounded-2.5xl border bg-page px-4 py-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-1 ${
        selected ? "border-brand-300 ring-2 ring-brand-100" : "border-line hover:border-brand-200"
      }`}
      onClick={() => onSelect(ticket)}
      type="button"
    >
      <p className="text-xs font-semibold leading-[18px] text-muted">{ticket.ticket_id}</p>
      <h3 className="mt-2 truncate text-sm font-semibold leading-5 text-ink">
        {ticket.title || ticket.summary || "未命名工单"}
      </h3>
      <p className="mt-2 truncate text-xs leading-[18px] text-muted">
        负责人 {ticket.assignee || "未分配"}
      </p>
    </button>
  );
}

function TicketColumn({ column, tickets, selectedId, onSelect }) {
  const visibleTickets = tickets.slice(0, 3);

  return (
    <section className="rounded-4xl border border-line bg-white p-5 shadow-card">
      <StatusChip tone={column.tone}>{column.title}</StatusChip>
      <div className="mt-4 space-y-3">
        {visibleTickets.length ? (
          visibleTickets.map((ticket) => (
            <TicketCard
              key={ticket.ticket_id}
              onSelect={onSelect}
              selected={ticket.ticket_id === selectedId}
              ticket={ticket}
            />
          ))
        ) : (
          <TicketCard ticket={null} />
        )}
      </div>
    </section>
  );
}

export function TicketsPanel({ data }) {
  const [tickets, setTickets] = useState(data.tickets);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(data.tickets[0]?.ticket_id ?? "");
  const selectedTicket = tickets.find((item) => item.ticket_id === selectedId);

  async function loadPage(nextOffset = 0) {
    setLoading(true);
    setError("");
    try {
      const page = await data.fetchTicketsPage({
        limit: DEFAULT_PAGE_SIZE,
        offset: nextOffset,
      });
      if (shouldReloadPreviousPage(page)) {
        await loadPage(previousPageOffset(page.offset, DEFAULT_PAGE_SIZE));
        return;
      }
      setTickets(page.items);
      setOffset(page.offset);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPage(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!tickets.length) {
      setSelectedId("");
      return;
    }
    if (!selectedId || !tickets.some((ticket) => ticket.ticket_id === selectedId)) {
      setSelectedId(tickets[0].ticket_id);
    }
  }, [tickets, selectedId]);

  const groupedTickets = useMemo(() => {
    return columns.map((column) => ({
      ...column,
      tickets: tickets.filter((ticket) => column.match.includes(ticket.status)),
    }));
  }, [tickets]);

  const todayCount = tickets.length;
  const processingCount = tickets.filter((ticket) => ticket.status === "In Progress").length;
  const resolvedCount = tickets.filter((ticket) =>
    ["Resolved", "Closed"].includes(ticket.status),
  ).length;
  const closeRate =
    tickets.length > 0 ? formatRate(resolvedCount / tickets.length) : "—";

  async function markSelectedResolved() {
    if (!selectedTicket) return;
    await data.updateTicket(selectedTicket.ticket_id, {
      status: "Resolved",
      assignee: selectedTicket.assignee,
      note: selectedTicket.note ?? "",
    });
    await loadPage(offset);
  }

  return (
    <div className="mt-9 space-y-6">
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {groupedTickets.map((column) => (
          <TicketColumn
            column={column}
            key={column.title}
            onSelect={(ticket) => setSelectedId(ticket.ticket_id)}
            selectedId={selectedId}
            tickets={column.tickets}
          />
        ))}
      </div>

      <section className="rounded-4xl bg-gradient-to-r from-brand-900 via-brand-600 to-sky-400 px-8 py-7 text-white shadow-card">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_440px] lg:items-center">
          <div>
            <h2 className="text-[20px] font-semibold leading-[28px]">
              工单不仅是待办，也是服务质量的复盘入口。
            </h2>
            <p className="mt-3 max-w-[560px] text-[13px] leading-[21px] text-blue-100">
              每个工单保留来源记录、客户上下文、处理备注与最终状态，便于管理者定位流程缺口。
            </p>
          </div>
          <div className="grid grid-cols-3 gap-8">
            {[
              ["当前页工单", displayMetric(todayCount, loading)],
              ["处理中", displayMetric(processingCount, loading)],
              ["关闭率", closeRate],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-xl font-semibold leading-[28px]">{value}</p>
                <p className="mt-1 text-xs leading-[18px] text-blue-200">{label}</p>
              </div>
            ))}
          </div>
        </div>
        {selectedTicket ? (
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <span className="text-sm text-blue-100">当前选中：{selectedTicket.ticket_id}</span>
            <button
              className="h-9 rounded-full bg-white px-4 text-sm font-semibold text-ink disabled:opacity-60"
              disabled={loading || data.ticketPending}
              onClick={markSelectedResolved}
              type="button"
            >
              标记完成
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );
}
