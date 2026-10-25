import { createFileRoute, Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronRight, Download, X } from "lucide-react";
import { Fragment, useId, useMemo, useState } from "react";
import { Metric } from "@/components/fixi/Metric";
import { AppShell, Card } from "@/components/fixi/AppShell";
import { Pill } from "@/components/fixi/Badge";
import { PropertyTabs } from "@/components/fixi/PropertyTabs";
import {
  QuotedByTradeDonut,
  QuotedByYearBars,
  RecurringIssuesList,
} from "@/components/fixi/PropertyStatsCharts";
import { usePropertyHistory, usePropertyStats } from "@/hooks/use-property-history";
import type { PropertyHistoryItem, Trade } from "@/api/types";
import { CASE_STATUSES, statusTone, type CaseStatus, STATUS_LABEL } from "@/lib/fixi-data";
import { formatDate, formatPence, titleCase } from "@/lib/format";
import { cn } from "@/lib/utils";
import { readParam } from "@/lib/search-params";
import { usePresentationMode } from "@/lib/presentation-mode";
import { presentationText } from "@/lib/presentation";

// `address`/`postcode` search params + the "no validateSearch" rule below
// are unchanged from the previous version of this file -- see that
// docstring, reproduced here because it's still exactly why this route reads
// search params by hand instead of through Route.useSearch().
//
// GET /api/v1/properties/{id}/history and .../stats are real, already-wired
// endpoints (backend/app/api/cases.py get_property_history /
// get_property_stats) -- unchanged by this rewrite. Everything new here
// (sorting, selection, export, drill-down filters) operates client-side on
// the same `items`/`statsData` these two hooks already return; no new
// backend route is needed for any of it.
export const Route = createFileRoute("/properties/$propertyId/history")({
  head: () => ({
    meta: [
      { title: "Property history — Fixi" },
      {
        name: "description",
        content: "Every maintenance case recorded for this property, from report to resolution.",
      },
      { property: "og:title", content: "Property history — Fixi" },
    ],
  }),
  component: HistoryPage,
});

type SortField = "date" | "category" | "cost" | "status";
type SortDir = "asc" | "desc";
interface SortState {
  field: SortField;
  dir: SortDir;
}

interface TableUrlState {
  sort: SortState;
  trade: Trade | null;
  year: number | null;
}

function readTableStateFromUrl(search: string): TableUrlState {
  const params = new URLSearchParams(search);
  const field = readParam(params, "sort");
  const dir = readParam(params, "dir");
  const trade = readParam(params, "trade");
  const yearRaw = readParam(params, "year");
  const year = yearRaw ? Number.parseInt(yearRaw, 10) : null;
  return {
    sort: {
      field: field === "category" || field === "cost" || field === "status" ? field : "date",
      dir: dir === "asc" ? "asc" : "desc",
    },
    trade: (trade as Trade | null) ?? null,
    year: year && Number.isFinite(year) ? year : null,
  };
}

const STATUS_RANK: Record<CaseStatus, number> = Object.fromEntries(
  CASE_STATUSES.map((s, i) => [s, i]),
) as Record<CaseStatus, number>;

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

function HistoryPage() {
  const { propertyId } = Route.useParams();
  const searchParams =
    typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;
  const address = readParam(searchParams, "address");
  const postcode = readParam(searchParams, "postcode");

  const history = usePropertyHistory(propertyId);
  const items = useMemo(() => history.data?.items ?? [], [history.data?.items]);
  const propertyStats = usePropertyStats(propertyId);
  const statsData = propertyStats.data;

  const searchStr = useRouterState({ select: (s) => s.location.searchStr });
  const tableState = useMemo(() => readTableStateFromUrl(searchStr), [searchStr]);
  // This route intentionally has no search validator. Keep unrelated search
  // values intact and let the router own history, including back/forward.
  const navigate = useNavigate() as unknown as (options: {
    search: (previous: Record<string, unknown>) => Record<string, unknown>;
    resetScroll: boolean;
    viewTransition: boolean;
  }) => Promise<void>;
  function setTableState(update: (state: TableUrlState) => TableUrlState) {
    const next = update(tableState);
    void navigate({
      search: (previous) => {
        const params: Record<string, unknown> = {
          ...previous,
          sort: next.sort.field,
          dir: next.sort.dir,
        };
        delete params["trade"];
        delete params["year"];
        if (next.trade) params["trade"] = next.trade;
        if (next.year) params["year"] = next.year;
        return params;
      },
      resetScroll: false,
      viewTransition: false,
    });
  }
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const trades = [...new Set(items.flatMap((h) => (h.trade ? [h.trade] : [])))].sort();
  const years = [...new Set(items.map((h) => new Date(h.created_at).getFullYear()))]
    .filter(Number.isFinite)
    .sort((a, b) => b - a);

  const filtered = useMemo(() => {
    return items.filter((h) => {
      if (tableState.trade && h.trade !== tableState.trade) return false;
      if (tableState.year && new Date(h.created_at).getFullYear() !== tableState.year) return false;
      return true;
    });
  }, [items, tableState.trade, tableState.year]);

  const sorted = useMemo(() => {
    const dirMul = tableState.sort.dir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      switch (tableState.sort.field) {
        case "date":
          return dirMul * a.created_at.localeCompare(b.created_at);
        case "category":
          return dirMul * (a.trade ?? "").localeCompare(b.trade ?? "");
        case "cost":
          return dirMul * ((a.quoted_pence ?? -1) - (b.quoted_pence ?? -1));
        case "status":
          return dirMul * (STATUS_RANK[a.status] - STATUS_RANK[b.status]);
        default:
          return 0;
      }
    });
  }, [filtered, tableState.sort]);

  // Selection tracks case ids; ids that fall out of the current filter stay
  // selected in state but simply aren't shown/counted here -- switching a
  // filter off restores them rather than silently discarding a choice.
  const visibleSelected = sorted.filter((h) => selected.has(h.case_id));
  const allVisibleSelected = sorted.length > 0 && visibleSelected.length === sorted.length;

  function toggleSort(field: SortField) {
    setTableState((s) =>
      s.sort.field === field
        ? { ...s, sort: { field, dir: s.sort.dir === "asc" ? "desc" : "asc" } }
        : { ...s, sort: { field, dir: "asc" } },
    );
  }

  function clearFilters() {
    setTableState((s) => ({ ...s, trade: null, year: null }));
  }

  function toggleRow(caseId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(caseId)) next.delete(caseId);
      else next.add(caseId);
      return next;
    });
  }

  function toggleSelectAllVisible() {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allVisibleSelected) {
        for (const h of sorted) next.delete(h.case_id);
      } else {
        for (const h of sorted) next.add(h.case_id);
      }
      return next;
    });
  }

  function exportSelectedCsv() {
    const rows = sorted.filter((h) => selected.has(h.case_id));
    if (rows.length === 0 || typeof window === "undefined") return;
    const header = ["Date", "Issue", "Trade", "Status", "Outcome", "Contractor", "Quoted"];
    const lines = [header.join(",")];
    for (const h of rows) {
      lines.push(
        [
          formatDate(h.created_at),
          h.title,
          h.trade ? titleCase(h.trade) : "",
          h.status,
          h.outcome ?? "",
          h.contractor_name ?? "",
          formatPence(h.quoted_pence) ?? "",
        ]
          .map(csvEscape)
          .join(","),
      );
    }
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `property-${propertyId}-history-export.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  const filteredQuotedTotal = filtered.reduce((sum, h) => sum + (h.quoted_pence ?? 0), 0);
  const hasActiveFilter = tableState.trade !== null || tableState.year !== null;

  const stats = [
    {
      value: propertyStats.isLoading
        ? "…"
        : propertyStats.isError
          ? "—"
          : String(statsData?.active_count ?? 0),
      label: "Active tickets",
    },
    {
      value: propertyStats.isLoading
        ? "…"
        : propertyStats.isError
          ? "—"
          : String(statsData?.total_count ?? 0),
      label: "Total tickets",
    },
    {
      value: propertyStats.isLoading
        ? "…"
        : propertyStats.isError
          ? "—"
          : String(statsData?.recurring_issues.length ?? 0),
      label: "Repeat issues",
    },
    {
      value: propertyStats.isLoading
        ? "…"
        : propertyStats.isError
          ? "—"
          : (statsData?.build_year?.toString() ?? "—"),
      label:
        !propertyStats.isLoading && !propertyStats.isError && statsData?.build_year == null
          ? "Build year unknown"
          : "Build year",
    },
  ];

  return (
    <AppShell>
      <PropertyTabs
        propertyId={propertyId}
        active="history"
        fallbackAddress={address}
        fallbackPostcode={postcode}
      >
        <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {stats.map((s) => (
            <Card key={s.label} className="px-4 py-3">
              <div className="text-metric font-bold tracking-tight">
                <Metric value={s.value} />
              </div>
              <div className="text-xs text-muted-foreground">{s.label}</div>
            </Card>
          ))}
        </section>

        <section className="mt-3 grid gap-3 xl:grid-cols-3">
          {propertyStats.isLoading ? (
            <Card className="p-4 xl:col-span-3">
              <p className="py-6 text-center text-xs text-muted-foreground">
                Loading property insights…
              </p>
            </Card>
          ) : propertyStats.isError ? (
            <Card className="p-4 xl:col-span-3">
              <p className="py-6 text-center text-xs text-destructive">
                Could not load property insights.
              </p>
            </Card>
          ) : (
            <>
              <QuotedByTradeDonut data={statsData?.quoted_by_trade ?? []} />
              <QuotedByYearBars data={statsData?.quoted_by_year ?? []} />
              <RecurringIssuesList data={statsData?.recurring_issues ?? []} />
            </>
          )}
        </section>

        <section aria-label="History filters" className="mt-5 flex flex-wrap items-end gap-3">
          <label className="grid gap-1 text-xs font-medium">
            Trade
            <select
              className="history-filter"
              value={tableState.trade ?? ""}
              onChange={(e) =>
                setTableState((s) => ({ ...s, trade: (e.target.value || null) as Trade | null }))
              }
            >
              <option value="">All trades</option>
              {tableState.trade && !trades.includes(tableState.trade) && (
                <option value={tableState.trade}>{titleCase(tableState.trade)}</option>
              )}
              {trades.map((trade) => (
                <option key={trade} value={trade}>
                  {titleCase(trade)}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-xs font-medium">
            Year
            <select
              className="history-filter"
              value={tableState.year ?? ""}
              onChange={(e) =>
                setTableState((s) => ({
                  ...s,
                  year: e.target.value ? Number(e.target.value) : null,
                }))
              }
            >
              <option value="">All years</option>
              {tableState.year && !years.includes(tableState.year) && (
                <option value={tableState.year}>{tableState.year}</option>
              )}
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </label>
          {hasActiveFilter && (
            <button
              type="button"
              onClick={clearFilters}
              className="flex h-9 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-xs font-medium hover:bg-accent"
            >
              <X className="h-3.5 w-3.5" /> Clear filters
            </button>
          )}
        </section>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="text-muted-foreground" role="status">
            Showing <b className="text-foreground">{sorted.length}</b> of {items.length} case
            {items.length === 1 ? "" : "s"}
            {" · "}
            <b className="text-foreground">{formatPence(filteredQuotedTotal) ?? "£0.00"}</b> quoted
          </div>
          {visibleSelected.length > 0 && (
            <button
              type="button"
              onClick={exportSelectedCsv}
              className="flex h-8 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-xs font-medium shadow-card hover:bg-accent"
            >
              <Download className="h-3.5 w-3.5" /> Export selected ({visibleSelected.length})
            </button>
          )}
        </div>

        <p className="mt-2 text-xs text-muted-foreground xl:hidden" id="history-scroll-hint">
          Scroll the table for outcomes, contractors and quotes.
        </p>
        <Card className="mt-2 overflow-hidden">
          <div
            role="region"
            aria-label="Property maintenance history"
            tabIndex={0}
            className="relative overflow-x-auto"
            aria-describedby="history-scroll-hint"
          >
            <table className="history-table w-full min-w-[1180px] table-fixed text-strong">
              <caption className="sr-only">
                Property maintenance history. Select cases to export their complete records.
              </caption>
              <colgroup>
                {[3.5, 10, 22, 9, 13, 18, 13, 8, 3.5].map((width, i) => (
                  <col key={i} style={{ width: `${width}%` }} />
                ))}
              </colgroup>
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="w-10 px-4 py-2.5">
                    <input
                      aria-label="Select all visible history rows"
                      type="checkbox"
                      className="accent-primary"
                      checked={allVisibleSelected}
                      onChange={toggleSelectAllVisible}
                      disabled={sorted.length === 0}
                    />
                  </th>
                  <SortableTh
                    field="date"
                    label="Date"
                    state={tableState.sort}
                    onSort={toggleSort}
                  />
                  <th className="px-4 py-2.5 font-medium">Issue</th>
                  <SortableTh
                    field="category"
                    label="Trade"
                    state={tableState.sort}
                    onSort={toggleSort}
                  />
                  <SortableTh
                    field="status"
                    label="Status"
                    state={tableState.sort}
                    onSort={toggleSort}
                  />
                  <th className="px-4 py-2.5 font-medium">Outcome</th>
                  <th className="px-4 py-2.5 font-medium">Contractor</th>
                  <SortableTh
                    field="cost"
                    label="Quoted"
                    state={tableState.sort}
                    onSort={toggleSort}
                  />
                  <th className="w-12 px-4 py-2.5 text-center font-medium">
                    <span className="sr-only">View</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {history.isLoading && (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-xs text-muted-foreground">
                      Loading history…
                    </td>
                  </tr>
                )}
                {history.isError && (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-xs text-destructive">
                      Could not load property history.
                    </td>
                  </tr>
                )}
                {!history.isLoading && !history.isError && items.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-xs text-muted-foreground">
                      No recorded cases for this property yet.
                    </td>
                  </tr>
                )}
                {!history.isLoading &&
                  !history.isError &&
                  items.length > 0 &&
                  sorted.length === 0 && (
                    <tr>
                      <td
                        colSpan={9}
                        className="px-4 py-8 text-center text-xs text-muted-foreground"
                      >
                        No cases match the current filter.
                      </td>
                    </tr>
                  )}
                {sorted.map((h) => (
                  <HistoryRow
                    key={h.case_id}
                    item={h}
                    selected={selected.has(h.case_id)}
                    onToggle={() => toggleRow(h.case_id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </PropertyTabs>
    </AppShell>
  );
}

function SortableTh({
  field,
  label,
  state,
  onSort,
}: {
  field: SortField;
  label: string;
  state: SortState;
  onSort: (field: SortField) => void;
}) {
  const active = state.field === field;
  return (
    <th
      className="px-4 py-2.5 font-medium"
      aria-sort={active ? (state.dir === "asc" ? "ascending" : "descending") : "none"}
    >
      <button
        type="button"
        onClick={() => onSort(field)}
        className={cn(
          "flex items-center gap-1 hover:text-foreground",
          field === "cost" && "ml-auto",
          active && "text-foreground",
        )}
      >
        {label}
        {active ? (
          state.dir === "asc" ? (
            <ArrowUp className="h-3 w-3" />
          ) : (
            <ArrowDown className="h-3 w-3" />
          )
        ) : (
          <ArrowUpDown className="h-3 w-3 opacity-40" />
        )}
      </button>
    </th>
  );
}

function HistoryRow({
  item: h,
  selected,
  onToggle,
}: {
  item: PropertyHistoryItem;
  selected: boolean;
  onToggle: () => void;
}) {
  const presentation = usePresentationMode();
  const [expanded, setExpanded] = useState(false);
  const detailsId = useId();
  return (
    <Fragment>
      <tr
        className={cn(
          "border-b border-border transition-colors hover:bg-muted/60",
          selected && "bg-selected",
        )}
      >
        <td>
          <input
            aria-label={`Select ${h.title}, ${formatDate(h.created_at)}`}
            type="checkbox"
            className="accent-primary"
            checked={selected}
            onChange={onToggle}
          />
        </td>
        <td className="tabular-nums text-muted-foreground">{formatDate(h.created_at)}</td>
        <td className="font-medium">
          <Link
            to="/maintenance/tickets/$ticketId/{-$section}"
            params={{ ticketId: h.case_id, section: undefined }}
            className="line-clamp-2 hover:underline"
          >
            {presentation ? presentationText(h.title) : h.title}
          </Link>
        </td>
        <td className="text-muted-foreground">{h.trade ? titleCase(h.trade) : "—"}</td>
        <td>
          <Pill tone={statusTone(h.status)}>{STATUS_LABEL[h.status] ?? h.status}</Pill>
        </td>
        <td>
          <p className="line-clamp-2 text-muted-foreground">
            {h.outcome ? (presentation ? presentationText(h.outcome) : h.outcome) : "Not recorded"}
          </p>
          <button
            type="button"
            aria-expanded={expanded}
            aria-controls={detailsId}
            aria-label={`${expanded ? "Hide" : "Read"} details for ${h.title}`}
            onClick={() => setExpanded(!expanded)}
            className="mt-1 min-h-7 text-xs font-medium text-primary underline underline-offset-4"
          >
            {expanded ? "Hide details" : "Read details"}
          </button>
        </td>
        <td className="text-muted-foreground">
          <span className="line-clamp-2">
            {h.contractor_name
              ? presentation
                ? presentationText(h.contractor_name)
                : h.contractor_name
              : "—"}
          </span>
          {!presentation && h.contractor_name?.includes("SIMULATED") && (
            <span className="text-micro font-medium">Simulated</span>
          )}
        </td>
        <td className="text-right font-medium tabular-nums">
          {formatPence(h.quoted_pence) ?? "—"}
        </td>
        <td>
          <Link
            to="/maintenance/tickets/$ticketId/{-$section}"
            params={{ ticketId: h.case_id, section: undefined }}
            aria-label={`Open case: ${h.title}`}
            className="inline-flex rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <ChevronRight className="h-4 w-4" />
          </Link>
        </td>
      </tr>
      <tr hidden={!expanded} id={detailsId} className="border-b border-border bg-muted/40">
        <td colSpan={9}>
          <div className="history-details grid gap-4 p-3 sm:grid-cols-[2fr_1fr]">
            <div>
              <h3 className="font-semibold">{h.title}</h3>
              <h4 className="mt-3 text-xs font-medium">Full outcome</h4>
              <p className="mt-1 whitespace-pre-wrap text-muted-foreground">
                {h.outcome ?? "No outcome recorded."}
              </p>
            </div>
            <div>
              <h4 className="text-xs font-medium">Contractor</h4>
              <p className="mt-1 text-muted-foreground">{h.contractor_name ?? "Not recorded"}</p>
              <h4 className="mt-3 text-xs font-medium">Quoted</h4>
              <p className="mt-1 tabular-nums">{formatPence(h.quoted_pence) ?? "Not recorded"}</p>
            </div>
          </div>
        </td>
      </tr>
    </Fragment>
  );
}
