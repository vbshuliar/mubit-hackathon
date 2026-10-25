import { Link } from "@tanstack/react-router";
import {
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  CheckCheck,
  CircleAlert,
  Layers3,
} from "lucide-react";
import type { ReactNode } from "react";
import type { CaseListItem, DashboardMetrics, UpcomingAppointmentItem } from "@/api/types";
import { PropertyPhoto } from "./PropertyTabs";
import { StatusBadge, UrgencyBadge } from "./Badge";
import { formatDateRange, formatRelative } from "@/lib/format";

export function OperationsDeck({
  metrics,
  metricsLoading,
  metricsError,
  items,
  loading,
  error,
  visits,
  visitsLoading,
  visitsError,
  onEscalated,
}: {
  metrics: DashboardMetrics | undefined;
  metricsLoading: boolean;
  metricsError: boolean;
  items: CaseListItem[];
  loading: boolean;
  error: boolean;
  visits: UpcomingAppointmentItem[];
  visitsLoading: boolean;
  visitsError: boolean;
  onEscalated: () => void;
}) {
  const attention = items.filter((item) => item.status === "ESCALATED").slice(0, 3);
  const states = metrics
    ? [
        { label: "Active", value: metrics.active, name: "active" },
        { label: "Confirming", value: metrics.awaiting_confirmation, name: "confirming" },
        { label: "Escalated", value: metrics.escalated, name: "escalated" },
        { label: "Resolved", value: metrics.resolved, name: "resolved" },
        { label: "Cancelled", value: metrics.cancelled, name: "cancelled" },
      ]
    : [];
  return (
    <div className="operations-deck">
      <section className="mission-panel" aria-labelledby="mission-title">
        <div className="mission-heading">
          <h2 id="mission-title">
            Every repair.
            <br />
            <span>In focus.</span>
          </h2>
          <span className="mission-emblem" aria-hidden="true">
            <Layers3 size={47} strokeWidth={0.8} />
          </span>
        </div>
        <div className="mission-stats" aria-label="Portfolio status">
          <div>
            <strong>{metrics ? metrics.active : "—"}</strong>
            <span>Active cases</span>
          </div>
          <div>
            <strong>{metrics ? metrics.awaiting_confirmation : "—"}</strong>
            <span>Awaiting confirmation</span>
          </div>
          <div>
            <strong>{metrics ? metrics.resolved_this_week : "—"}</strong>
            <span>Resolved this week</span>
          </div>
        </div>
        {metricsLoading ? (
          <p className="mission-state">Loading portfolio status…</p>
        ) : metricsError ? (
          <p className="mission-state" role="alert">
            Portfolio metrics unavailable. Try refreshing the page.
          </p>
        ) : metrics ? (
          <>
            <div
              className="mission-distribution"
              role="img"
              aria-label={states.map((s) => `${s.value} ${s.label}`).join(", ")}
            >
              {states.map((s) => (
                <span
                  key={s.name}
                  className={`distribution-${s.name}`}
                  style={{ flexGrow: s.value }}
                />
              ))}
            </div>
            <div className="mission-foot">
              <span>{metrics.total} total tickets</span>
              <span>
                {metrics.avg_resolution_hours === null
                  ? "No resolution average yet"
                  : `${metrics.avg_resolution_hours.toFixed(1)}h average · last 30 days`}
              </span>
            </div>
          </>
        ) : null}
      </section>
      <section className="attention-inbox" aria-labelledby="attention-title">
        <div className="deck-heading">
          <h2 id="attention-title">
            <CircleAlert size={17} />
            Needs attention
          </h2>
          <button onClick={onEscalated} type="button">
            View escalated <ArrowUpRight size={14} />
          </button>
        </div>
        {loading ? (
          <p className="deck-empty">Loading escalations…</p>
        ) : error ? (
          <p className="deck-empty" role="alert">
            Could not load cases. Refresh to try again.
          </p>
        ) : attention.length === 0 ? (
          <div className="deck-empty">
            <CheckCheck size={27} />
            <p>No escalated cases in these results.</p>
            <span>Change the queue filters to see more cases.</span>
          </div>
        ) : (
          <div className="attention-items">
            {attention.map((item) => (
              <Link
                key={item.id}
                to="/maintenance/tickets/$ticketId/{-$section}"
                params={{ ticketId: item.id, section: undefined }}
                className="attention-item"
              >
                <span className="attention-number">#{item.case_number}</span>
                <div>
                  <h3>{item.title}</h3>
                  <p>{item.property_address}</p>
                </div>
                <ArrowUpRight size={16} />
              </Link>
            ))}
          </div>
        )}
        <div className="attention-foot">
          <span className="attention-dot" />
          Escalations from the loaded queue · review before acting
        </div>
      </section>
      <section className="visit-rail" aria-labelledby="visit-title">
        <div className="deck-heading">
          <h2 id="visit-title">
            <CalendarDays size={17} />
            Next visits
          </h2>
          <span>{visits.length ? `${visits.length} shown` : ""}</span>
        </div>
        {visitsLoading ? (
          <p className="deck-empty">Loading visits…</p>
        ) : visitsError ? (
          <p className="deck-empty" role="alert">
            Could not load scheduled visits.
          </p>
        ) : visits.length === 0 ? (
          <div className="visit-empty">
            <CalendarDays size={32} strokeWidth={1} />
            <h3>A clear schedule.</h3>
            <p>No upcoming confirmed visits. Scheduled appointments will appear here.</p>
          </div>
        ) : (
          <div className="visit-list">
            {visits.map((v) => (
              <Link
                key={v.appointment_id}
                to="/maintenance/tickets/$ticketId/{-$section}"
                params={{ ticketId: v.case_id, section: undefined }}
              >
                <time dateTime={v.start_at}>
                  <strong>{new Date(v.start_at).getDate()}</strong>
                  <span>
                    {new Date(v.start_at).toLocaleDateString(undefined, { month: "short" })}
                  </span>
                </time>
                <div>
                  <h3>{v.property_address}</h3>
                  <p>{formatDateRange(v.start_at, v.end_at).time}</p>
                  <span>{v.contractor_name}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
        <Link to="/properties" className="visit-footer">
          Explore your properties <ArrowRight size={15} />
        </Link>
      </section>
    </div>
  );
}

const lanes = [
  { id: "attention", title: "Escalated", subtitle: "Operator review", statuses: ["ESCALATED"] },
  { id: "active", title: "In progress", subtitle: "Coordination & delivery", statuses: ["ACTIVE"] },
  {
    id: "confirming",
    title: "Confirming",
    subtitle: "Awaiting the tenant",
    statuses: ["AWAITING_CONFIRMATION"],
  },
  {
    id: "closed",
    title: "Closed",
    subtitle: "Resolved & cancelled",
    statuses: ["RESOLVED", "CANCELLED"],
  },
];

export function CaseBoard({
  items,
  loading,
  error,
  renderActions,
}: {
  items: CaseListItem[];
  loading: boolean;
  error: boolean;
  renderActions: (item: CaseListItem) => ReactNode;
}) {
  if (loading)
    return (
      <div className="board-message" role="status">
        Loading the repair board…
      </div>
    );
  if (error)
    return (
      <div className="board-message" role="alert">
        Could not load tickets. Refresh the page to try again.
      </div>
    );
  if (items.length === 0)
    return <div className="board-message">No tickets match your filters.</div>;
  return (
    <div className="case-board" aria-label="Repair workflow board">
      {lanes.map((lane) => {
        const cards = items.filter((item) => lane.statuses.includes(item.status));
        return (
          <section key={lane.id} className={`board-lane lane-${lane.id}`} aria-label={lane.title}>
            <header>
              <div>
                <h3>
                  <span />
                  {lane.title}
                  <b>{cards.length}</b>
                </h3>
                <p>{lane.subtitle}</p>
              </div>
            </header>
            <div
              className="lane-cards"
              tabIndex={cards.length > 3 ? 0 : undefined}
              aria-label={`${lane.title} cases`}
            >
              {cards.length === 0 ? (
                <p className="lane-empty">No cases here</p>
              ) : (
                cards.map((item) => (
                  <article className="board-case" key={item.id}>
                    <div className="board-case-top">
                      <span>
                        #{item.case_number} ·{" "}
                        {item.category ? item.category.toLowerCase() : "Uncategorised"}
                      </span>
                      {renderActions(item)}
                    </div>
                    <Link
                      to="/maintenance/tickets/$ticketId/{-$section}"
                      params={{ ticketId: item.id, section: undefined }}
                      className="board-case-title"
                    >
                      {item.title}
                      <ArrowUpRight size={15} />
                    </Link>
                    <div className="board-property">
                      <PropertyPhoto
                        photoKey={item.property_photo_key}
                        className="h-8 w-8 rounded-md"
                      />
                      <span>{item.property_address}</span>
                    </div>
                    <div className="board-case-tags">
                      <UrgencyBadge urgency={item.urgency} />
                      {lane.id === "closed" && <StatusBadge status={item.status} />}
                      {item.is_archived && <span className="sample-label">Archival sample</span>}
                    </div>
                    <footer>
                      <span>{item.assigned_contractor_name ?? "Awaiting assignment"}</span>
                      <time dateTime={item.updated_at}>{formatRelative(item.updated_at)}</time>
                    </footer>
                  </article>
                ))
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}
