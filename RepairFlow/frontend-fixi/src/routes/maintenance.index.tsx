import * as Dialog from "@radix-ui/react-dialog";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { createFileRoute, Link } from "@tanstack/react-router";
import { LayoutGrid, List, ChevronDown, ChevronRight, MoreHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import { AppShell, Card } from "@/components/fixi/AppShell";
import { PropertyPhoto } from "@/components/fixi/PropertyTabs";
import { StatusBadge, UrgencyBadge } from "@/components/fixi/Badge";
import { CaseBoard, OperationsDeck } from "@/components/fixi/OperationsDeck";
import { Skeleton, SkeletonCards } from "@/components/fixi/Skeleton";
import { Button } from "@/components/ui/button";
import { useCancelCase } from "@/hooks/use-case-actions";
import { useCaseList } from "@/hooks/use-case-list";
import { useDashboardMetrics } from "@/hooks/use-dashboard-metrics";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { usePropertyOptions } from "@/hooks/use-new-ticket";
import { useUpcomingAppointments } from "@/hooks/use-upcoming-appointments";
import { useCaseSearch } from "@/lib/case-search-context";
import {
  CASE_STATUSES,
  STATUS_LABEL,
  URGENCIES,
  URGENCY_LABEL,
  type CaseStatus,
  type Urgency,
} from "@/lib/fixi-data";
import { formatRelative } from "@/lib/format";
import { cn } from "@/lib/utils";

// One entry per <colgroup> column, in order: select, number, issue,
// property, urgency, status, assignee, updated, menu. `null` means the
// column carries only an icon or control, so a bar there would be noise.
const SKELETON_CELLS: readonly (string | null)[] = [
  null,
  "w-6",
  "w-4/5",
  "w-14",
  "w-24",
  "w-28",
  "w-16",
  null,
];

export const Route = createFileRoute("/maintenance/")({
  head: () => ({
    meta: [
      { title: "Maintenance — Fixi" },
      {
        name: "description",
        content:
          "All property issues, from report to resolution. Track open, in-progress and resolved maintenance tickets.",
      },
      { property: "og:title", content: "Maintenance — Fixi" },
      { property: "og:description", content: "All property issues, from report to resolution." },
    ],
  }),
  component: MaintenancePage,
});

const statusFilters: Array<{ label: string; value: CaseStatus | "ALL" }> = [
  { label: "All", value: "ALL" },
  ...CASE_STATUSES.map((s) => ({ label: STATUS_LABEL[s], value: s })),
];

function MaintenancePage() {
  const [view, setView] = useState<"board" | "list">("board");
  const [statusFilter, setStatusFilter] = useState<CaseStatus | "ALL">("ALL");
  const [urgencyFilter, setUrgencyFilter] = useState<Urgency | "ALL">("ALL");
  const [propertyFilter, setPropertyFilter] = useState<string | "ALL">("ALL");
  const [contractorFilter, setContractorFilter] = useState<string | "ALL">("ALL");
  // Off by default, matching the API and every other directory screen:
  // archival sample history must never walk into an operational queue
  // uninvited. But with it permanently off there was no route from this
  // list to the ~60 closed sample cases at all -- they exist, they carry
  // full histories, and the only ways in were Insights, Reports, a
  // property's history or global search. Every archival row this returns
  // is badged, so one can't be mistaken for work to do.
  const [includeArchived, setIncludeArchived] = useState(false);

  // Global search box lives in UtilityBar (rendered once, inside AppShell,
  // above every page) -- its value comes through CaseSearchContext rather
  // than local state so it can be set from outside this component.
  const { search } = useCaseSearch();
  const debouncedSearch = useDebouncedValue(search, 300);

  const metrics = useDashboardMetrics();
  const properties = usePropertyOptions();
  const upcoming = useUpcomingAppointments();
  const cases = useCaseList({
    status: statusFilter === "ALL" ? undefined : statusFilter,
    property_id: propertyFilter === "ALL" ? undefined : propertyFilter,
    q: debouncedSearch.trim() || undefined,
    include_archived: includeArchived || undefined,
    limit: includeArchived ? 100 : undefined,
  });

  // Contractor filter has no honest server-side id to filter on: the case
  // list only carries assigned_contractor_name (no id), and the demo seed
  // refs only expose two specific contractor ids (roofer_id/scaffolder_id),
  // not a full roster -- there are >=3 seeded contractors. Rather than
  // build a filter that's silently wrong for the contractor(s) missing an
  // id, this filters client-side by name over whatever's on the current
  // page of results (same honesty tradeoff docs/26 would want recorded).
  const contractorOptions = useMemo(() => {
    const names = new Set<string>();
    for (const c of cases.data?.items ?? []) {
      if (c.assigned_contractor_name) names.add(c.assigned_contractor_name);
    }
    // Keep the active selection in the list even if a status/property
    // change makes it disappear from the current page -- otherwise the
    // <select> would show a blank value instead of the chosen contractor.
    if (contractorFilter !== "ALL") names.add(contractorFilter);
    return Array.from(names).sort();
  }, [cases.data, contractorFilter]);

  const items = useMemo(() => {
    return (cases.data?.items ?? []).filter((c) => {
      if (urgencyFilter !== "ALL" && c.urgency !== urgencyFilter) return false;
      if (contractorFilter !== "ALL" && c.assigned_contractor_name !== contractorFilter) {
        return false;
      }
      return true;
    });
  }, [cases.data, urgencyFilter, contractorFilter]);

  // Real CONFIRMED visits across every case, soonest first (backend already
  // sorts); capped here so the sidebar card can't grow unbounded as more
  // demo cases get seeded.
  const visits = (upcoming.data?.items ?? []).slice(0, 5);

  return (
    <AppShell>
      <div className="operations-page mx-auto max-w-page px-6 py-4 xl:px-7">
        <header className="operations-header">
          <div>
            <h1>Maintenance</h1>
            <p>Your repairs, their dependencies and the decisions that move them forward.</p>
          </div>
          <div className="operations-date">
            <span />
            Operator workspace
          </div>
        </header>
        <OperationsDeck
          metrics={metrics.data}
          metricsLoading={metrics.isLoading}
          metricsError={metrics.isError}
          items={items}
          loading={cases.isLoading}
          error={cases.isError}
          visits={visits}
          visitsLoading={upcoming.isLoading}
          visitsError={upcoming.isError}
          onEscalated={() => setStatusFilter("ESCALATED")}
        />
        <section className="queue-workspace" aria-label="Case queue">
          <div className="queue-toolbar">
            <div>
              <h2>Repair workspace</h2>
              <p>
                {cases.isLoading
                  ? "Loading cases…"
                  : cases.isError
                    ? "Queue unavailable"
                    : `${items.length} loaded cases`}
                {cases.data?.next_cursor ? " · more available through search" : ""}
              </p>
            </div>
            <div className="queue-view-toggle" role="group" aria-label="Queue view">
              <button
                type="button"
                aria-pressed={view === "board"}
                onClick={() => setView("board")}
              >
                <LayoutGrid size={15} />
                Board
              </button>
              <button type="button" aria-pressed={view === "list"} onClick={() => setView("list")}>
                <List size={15} />
                List
              </button>
            </div>
          </div>
          <section className="queue-filterbar mt-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-1.5">
              {statusFilters.map((f) => (
                <button
                  key={f.value}
                  aria-pressed={statusFilter === f.value}
                  onClick={() => setStatusFilter(f.value)}
                  className={cn(
                    "min-h-9 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                    statusFilter === f.value
                      ? "border-foreground bg-foreground text-background"
                      : "border-border bg-card text-foreground hover:bg-accent",
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <details className="advanced-filters w-full">
              <summary>
                Advanced filters
                {urgencyFilter !== "ALL" ||
                propertyFilter !== "ALL" ||
                contractorFilter !== "ALL" ||
                includeArchived
                  ? " · filters applied"
                  : ""}
              </summary>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <FilterDropdown
                  value={urgencyFilter}
                  onChange={setUrgencyFilter}
                  allLabel="All urgencies"
                  options={URGENCIES.map((u) => ({ value: u, label: URGENCY_LABEL[u] }))}
                />
                <FilterDropdown
                  value={propertyFilter}
                  onChange={setPropertyFilter}
                  allLabel="All properties"
                  options={(properties.data?.items ?? []).map((p) => ({
                    value: p.id,
                    label: p.address_line,
                  }))}
                />
                <FilterDropdown
                  value={contractorFilter}
                  onChange={setContractorFilter}
                  allLabel="All contractors"
                  options={contractorOptions.map((name) => ({ value: name, label: name }))}
                />
                <label className="flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-xs font-medium text-foreground hover:bg-accent">
                  <input
                    type="checkbox"
                    className="accent-primary"
                    checked={includeArchived}
                    aria-label="Include archival sample history"
                    onChange={(e) => setIncludeArchived(e.target.checked)}
                  />
                  Include archival sample history
                </label>
              </div>
              <p className="mt-3 text-micro text-muted-foreground">
                Urgency and contractor filters apply to the loaded results. Archival sample history
                loads up to 100 records.
              </p>
            </details>
          </section>

          {view === "board" ? (
            <CaseBoard
              items={items}
              loading={cases.isLoading}
              error={cases.isError}
              renderActions={(t) => (
                <RowActions
                  caseId={t.id}
                  caseNumber={t.case_number}
                  status={t.status}
                  version={t.version}
                />
              )}
            />
          ) : (
            <div className="mt-3 grid items-start gap-5">
              <Card className="queue-desktop overflow-x-auto">
                <table
                  className="w-full min-w-[1050px] table-fixed text-body"
                  aria-label="Repair case queue"
                >
                  <colgroup>
                    <col className="w-[54px]" />
                    <col className="w-[62px]" />
                    <col />
                    <col className="w-[100px]" />
                    <col className="w-[180px]" />
                    <col className="w-[195px]" />
                    <col className="w-[88px]" />
                    <col className="w-[44px]" />
                  </colgroup>
                  <thead>
                    <tr className="border-b border-border bg-muted/50 text-left text-muted-foreground">
                      <th scope="col">
                        <span className="sr-only">Property photo</span>
                      </th>
                      {[
                        "Case",
                        "Issue / property",
                        "Urgency",
                        "Status",
                        "Assigned to",
                        "Updated",
                      ].map((label) => (
                        <th scope="col" key={label} className="px-3 py-3 text-micro font-medium">
                          {label}
                        </th>
                      ))}
                      <th scope="col">
                        <span className="sr-only">Actions</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {cases.isLoading &&
                      Array.from({ length: 8 }).map((_, r) => (
                        <tr key={r} className="h-20 border-b border-border">
                          {SKELETON_CELLS.map((w, c) => (
                            <td key={c} className="px-3">
                              {w ? <Skeleton className={cn("h-3", w)} /> : null}
                            </td>
                          ))}
                        </tr>
                      ))}
                    {cases.isError && (
                      <tr>
                        <td colSpan={8} className="px-4 py-8 text-center text-destructive">
                          Could not load tickets. Is the backend running?
                        </td>
                      </tr>
                    )}
                    {!cases.isLoading && !cases.isError && items.length === 0 && (
                      <tr>
                        <td colSpan={8} className="px-4 py-8 text-center text-muted-foreground">
                          No tickets match the current filters.
                        </td>
                      </tr>
                    )}
                    {items.map((t) => (
                      <tr
                        key={t.id}
                        className="border-b border-border last:border-0 transition-colors hover:bg-muted/50"
                      >
                        <td className="pl-4 py-4">
                          <PropertyPhoto
                            photoKey={t.property_photo_key}
                            className="h-9 w-9 rounded-md"
                          />
                        </td>
                        <td className="px-3 py-4 text-micro text-muted-foreground">
                          <Link
                            to="/maintenance/tickets/$ticketId/{-$section}"
                            params={{ ticketId: t.id, section: undefined }}
                          >
                            #{t.case_number}
                          </Link>
                        </td>
                        <td className="px-3 py-4">
                          <Link
                            to="/maintenance/tickets/$ticketId/{-$section}"
                            params={{ ticketId: t.id, section: undefined }}
                            className="queue-title block font-medium hover:underline"
                          >
                            {t.title}
                          </Link>
                          <p className="mt-1 text-micro text-muted-foreground">
                            {t.property_address}
                          </p>
                          {t.is_archived && <span className="sample-label">Archival sample</span>}
                        </td>
                        <td className="px-3 py-4">
                          <UrgencyBadge urgency={t.urgency} />
                        </td>
                        <td className="px-3 py-4">
                          <StatusBadge status={t.status} />
                        </td>
                        <td className="px-3 py-4 text-micro text-muted-foreground break-words">
                          {t.assigned_contractor_name ?? "Unassigned"}
                        </td>
                        <td className="px-3 py-4 text-micro text-muted-foreground">
                          {formatRelative(t.updated_at)}
                        </td>
                        <td className="px-2 py-4">
                          <RowActions
                            caseId={t.id}
                            caseNumber={t.case_number}
                            status={t.status}
                            version={t.version}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
              <div className="queue-mobile" aria-label="Repair case queue">
                {cases.isLoading && <SkeletonCards count={4} height="h-44" />}
                {cases.isError && (
                  <p role="alert" className="py-6 text-destructive">
                    Could not load tickets. Is the backend running?
                  </p>
                )}
                {!cases.isLoading && !cases.isError && items.length === 0 && (
                  <p className="py-6 text-muted-foreground">
                    No tickets match the current filters.
                  </p>
                )}
                {items.map((t) => (
                  <article key={t.id} className="mobile-case">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-micro text-muted-foreground">
                        #{t.case_number} · {formatRelative(t.updated_at)}
                      </span>
                      <RowActions
                        caseId={t.id}
                        caseNumber={t.case_number}
                        status={t.status}
                        version={t.version}
                      />
                    </div>
                    <Link
                      to="/maintenance/tickets/$ticketId/{-$section}"
                      params={{ ticketId: t.id, section: undefined }}
                      className="mt-2 block text-base font-medium leading-snug hover:underline"
                    >
                      {t.title}
                    </Link>
                    <p className="mt-2 text-sm text-muted-foreground">{t.property_address}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <StatusBadge status={t.status} />
                      <UrgencyBadge urgency={t.urgency} />
                      {t.is_archived && <span className="sample-label">Archival sample</span>}
                    </div>
                    <p className="mt-3 text-micro text-muted-foreground">
                      Assigned to {t.assigned_contractor_name ?? "nobody yet"}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}

/** Row-level "…" menu.
 *
 * Offers only the actions the legal transition graph permits from this
 * row's status. Hard delete is deliberately absent: it existed to reset a
 * rehearsed demo, and permanently destroying a case -- with its events,
 * calls and work orders -- is not something a list row should offer.
 * Cancel closes a case without a repair outcome and keeps the record.
 *
 * Each row needs its own mutation instance (they are keyed on caseId), so
 * this is a component rather than inline JSX inside the .map().
 */
function RowActions({
  caseId,
  caseNumber,
  status,
  version,
}: {
  caseId: string;
  caseNumber: number;
  status: CaseStatus;
  version: number;
}) {
  const cancel = useCancelCase(caseId);
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const canCancel =
    status === "ACTIVE" || status === "AWAITING_CONFIRMATION" || status === "ESCALATED";

  async function submit() {
    if (!reason.trim()) return;
    setError(null);
    try {
      await cancel.mutateAsync({ version, reason: reason.trim() });
      setOpen(false);
      setReason("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "That case could not be cancelled.");
    }
  }

  return (
    <>
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild>
          <button
            type="button"
            aria-label={`Actions for ticket #${caseNumber}`}
            disabled={cancel.isPending}
            className="rounded-md p-1 text-muted-foreground hover:bg-accent disabled:opacity-50"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            align="end"
            className="z-50 min-w-[180px] rounded-lg border border-border bg-card p-1 shadow-panel"
          >
            <DropdownMenu.Item asChild>
              <Link
                to="/maintenance/tickets/$ticketId/{-$section}"
                params={{ ticketId: caseId, section: undefined }}
                className="block cursor-pointer rounded-md px-2.5 py-1.5 text-xs font-medium outline-none hover:bg-accent data-[highlighted]:bg-accent"
              >
                Open ticket
              </Link>
            </DropdownMenu.Item>
            <DropdownMenu.Item asChild>
              <Link
                to="/messages/$caseId"
                params={{ caseId }}
                className="block cursor-pointer rounded-md px-2.5 py-1.5 text-xs font-medium outline-none hover:bg-accent data-[highlighted]:bg-accent"
              >
                Open conversation
              </Link>
            </DropdownMenu.Item>
            {canCancel ? (
              <DropdownMenu.Item
                onSelect={() => {
                  setError(null);
                  setOpen(true);
                }}
                className="cursor-pointer rounded-md px-2.5 py-1.5 text-xs font-medium text-destructive outline-none hover:bg-destructive/10 data-[highlighted]:bg-destructive/10"
              >
                Cancel case
              </DropdownMenu.Item>
            ) : (
              <div className="px-2.5 py-1.5 text-micro text-muted-foreground">
                This case is {STATUS_LABEL[status].toLowerCase()} — it cannot be cancelled.
              </div>
            )}
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>

      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-foreground/25 backdrop-blur-[1px]" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(26rem,92vw)] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-border bg-card p-5 shadow-panel">
            <Dialog.Title className="text-section font-semibold">
              Cancel ticket #{caseNumber}
            </Dialog.Title>
            <Dialog.Description className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Closes the case without a repair outcome. The case and its history stay readable —
              nothing is deleted.
            </Dialog.Description>
            <label className="mt-4 block">
              <span className="text-xs font-medium">
                Reason<span className="text-destructive"> *</span>
              </span>
              <textarea
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Recorded on the case timeline."
                className="mt-1 w-full resize-y rounded-lg border border-border bg-background px-2.5 py-2 text-xs outline-none focus:ring-2 focus:ring-ring"
              />
            </label>
            {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
            <div className="mt-4 flex justify-end gap-2">
              <Dialog.Close asChild>
                <Button variant="ghost" size="sm" disabled={cancel.isPending}>
                  Keep open
                </Button>
              </Dialog.Close>
              <Button
                size="sm"
                variant="destructive"
                disabled={cancel.isPending || !reason.trim()}
                title={reason.trim() ? undefined : "A reason is required"}
                onClick={() => void submit()}
              >
                {cancel.isPending ? "Cancelling…" : "Cancel case"}
              </Button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
function FilterDropdown<T extends string>({
  value,
  onChange,
  allLabel,
  options,
}: {
  value: T | "ALL";
  onChange: (v: T | "ALL") => void;
  allLabel: string;
  options: Array<{ value: T; label: string }>;
}) {
  return (
    <label className="flex h-8 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-xs font-medium text-foreground hover:bg-accent">
      {/* appearance-none drops the browser's own arrow so only the
       * ChevronDown below renders -- without it the native select arrow
       * and this icon would both show. */}
      <select
        className="max-w-[160px] truncate appearance-none bg-transparent outline-none"
        value={value}
        onChange={(e) => onChange(e.target.value as T | "ALL")}
      >
        <option value="ALL">{allLabel}</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
    </label>
  );
}
