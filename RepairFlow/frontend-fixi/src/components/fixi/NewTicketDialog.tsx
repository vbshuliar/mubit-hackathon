import type { SafetyAnswer, SafetyAnswers } from "@/api/types";
import { SAFETY_FIELDS, validAvailability } from "@/lib/demo-response";
import * as Dialog from "@radix-ui/react-dialog";
import { useNavigate } from "@tanstack/react-router";
import { Plus, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { useCreateTicket, usePropertyOptions, useTenantOptions } from "@/hooks/use-new-ticket";

/** Text intake for a simulated repair, using the real domain and agent workflow. */

const CATEGORIES = [
  { value: "", label: "Not sure yet" },
  { value: "ROOFING", label: "Roofing" },
  { value: "PLUMBING", label: "Plumbing" },
  { value: "ELECTRICAL", label: "Electrical" },
  { value: "SCAFFOLDING", label: "Scaffolding" },
  { value: "OTHER", label: "Other" },
] as const;

const fieldClass =
  "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring disabled:opacity-50";
const labelClass = "block text-xs font-medium text-muted-foreground";

export function NewTicketDialog() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [propertyId, setPropertyId] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [category, setCategory] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [touched, setTouched] = useState(false);
  const [safety, setSafety] = useState<SafetyAnswers>({});
  const [hasAvailability, setHasAvailability] = useState(false);
  const [availableFrom, setAvailableFrom] = useState("");
  const [availableUntil, setAvailableUntil] = useState("");

  const properties = usePropertyOptions();
  const tenants = useTenantOptions(propertyId || null);
  const createTicket = useCreateTicket();

  const propertyItems = useMemo(() => properties.data?.items ?? [], [properties.data]);
  const tenantItems = useMemo(() => tenants.data?.items ?? [], [tenants.data]);

  // Picking a different property invalidates the tenant choice.
  useEffect(() => {
    setTenantId("");
  }, [propertyId]);

  // With exactly one tenant there is no ambiguity, so preselect — but only
  // then. Two tenants means the operator has to say which one.
  useEffect(() => {
    if (tenantItems.length === 1 && tenantId === "") {
      setTenantId(tenantItems[0]!.id);
    }
  }, [tenantItems, tenantId]);

  const errors = {
    availability:
      !hasAvailability || validAvailability(availableFrom, availableUntil)
        ? null
        : "Choose an availability window ending in the future, after its start.",
    property: propertyId ? null : "Choose a property.",
    tenant: tenantId ? null : "Choose which tenant reported this.",
    location: location.trim() ? null : "Say where in the property the issue is.",
    description:
      description.trim().length >= 8
        ? null
        : "Describe the issue in at least a few words — this is what triage reads.",
  };
  const canSubmit = Object.values(errors).every((e) => e === null);

  function reset() {
    setPropertyId("");
    setTenantId("");
    setCategory("");
    setLocation("");
    setDescription("");
    setTouched(false);
    setSafety({});
    setHasAvailability(false);
    setAvailableFrom("");
    setAvailableUntil("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (!canSubmit) return;
    try {
      const created = await createTicket.mutateAsync({
        simulated: true,
        safety_answers: safety,
        ...(hasAvailability
          ? {
              availability: [
                {
                  start_at: new Date(availableFrom).toISOString(),
                  end_at: new Date(availableUntil).toISOString(),
                  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                  spoken_text: "Tenant confirmed this availability during the simulated intake.",
                  confirmed_by_speaker: true,
                },
              ],
            }
          : {}),
        property_id: propertyId,
        tenant_id: tenantId,
        description: description.trim(),
        location: location.trim(),
        source_text: description.trim(),
        ...(category ? { category: category as OperatorIntakeCategory } : {}),
      });
      reset();
      setOpen(false);
      // Land on the case that was just created; raising a ticket and then
      // having to hunt for it in the list is the wrong ending.
      void navigate({
        to: "/maintenance/tickets/$ticketId/{-$section}",
        params: { ticketId: created.case_id, section: undefined },
      });
    } catch {
      // Surfaced by the hook's onError toast; the dialog stays open with
      // the operator's text intact so they can correct and retry.
    }
  }

  const showError = (key: keyof typeof errors) => touched && errors[key];

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <Dialog.Trigger asChild>
        <Button className="rounded-xl px-4">
          <Plus /> New Ticket
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-foreground/25 backdrop-blur-[1px]" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[90vh] w-[min(30rem,92vw)] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-2xl border border-border bg-card p-6 shadow-panel">
          <div className="flex items-start justify-between gap-3">
            <div>
              <Dialog.Title className="text-section font-semibold text-foreground">
                New demo repair ticket
              </Dialog.Title>
              <Dialog.Description className="mt-1 text-xs leading-relaxed text-muted-foreground">
                Describe a simulated repair. The agent makes real decisions; tenant and specialist
                responses are entered as text. Nobody is contacted.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <Button variant="ghost" size="iconSm" aria-label="Close">
                <X />
              </Button>
            </Dialog.Close>
          </div>

          <form onSubmit={(e) => void handleSubmit(e)} noValidate>
            <div className="mt-4">
              <label className={labelClass} htmlFor="new-ticket-property">
                Property
              </label>
              <select
                id="new-ticket-property"
                className={fieldClass}
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                disabled={properties.isLoading}
                aria-invalid={showError("property") ? true : undefined}
              >
                <option value="">
                  {properties.isLoading ? "Loading properties…" : "Select a property…"}
                </option>
                {propertyItems.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.address_line}, {p.postcode}
                  </option>
                ))}
              </select>
              {showError("property") && (
                <p className="mt-1 text-micro text-destructive">{errors.property}</p>
              )}
              {!properties.isLoading && propertyItems.length === 0 && (
                <p className="mt-1 text-micro text-muted-foreground">
                  No properties yet — add one under Properties before raising a ticket.
                </p>
              )}
              {properties.isError && (
                <p className="mt-1 text-micro text-destructive">
                  Could not load properties. Is the backend running?
                </p>
              )}
            </div>

            <div className="mt-3">
              <label className={labelClass} htmlFor="new-ticket-tenant">
                Reported by
              </label>
              <select
                id="new-ticket-tenant"
                className={fieldClass}
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                disabled={!propertyId || tenants.isLoading}
                aria-invalid={showError("tenant") ? true : undefined}
              >
                <option value="">
                  {!propertyId
                    ? "Choose a property first"
                    : tenants.isLoading
                      ? "Loading tenants…"
                      : "Select a tenant…"}
                </option>
                {tenantItems.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.display_name}
                  </option>
                ))}
              </select>
              {showError("tenant") && (
                <p className="mt-1 text-micro text-destructive">{errors.tenant}</p>
              )}
              {propertyId && !tenants.isLoading && tenantItems.length === 0 && (
                <p className="mt-1 text-micro text-muted-foreground">
                  No tenant recorded at this property yet — add one under Tenants.
                </p>
              )}
            </div>

            <div className="mt-3 grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass} htmlFor="new-ticket-location">
                  Location
                </label>
                <input
                  id="new-ticket-location"
                  className={fieldClass}
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. rear bedroom ceiling"
                  aria-invalid={showError("location") ? true : undefined}
                />
                {showError("location") && (
                  <p className="mt-1 text-micro text-destructive">{errors.location}</p>
                )}
              </div>
              <div>
                <label className={labelClass} htmlFor="new-ticket-category">
                  Category
                </label>
                <select
                  id="new-ticket-category"
                  className={fieldClass}
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-3">
              <label className={labelClass} htmlFor="new-ticket-description">
                What was reported?
              </label>
              <textarea
                id="new-ticket-description"
                className={`${fieldClass} h-24 resize-y`}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="In the reporter's own words where possible — this is what safety triage reads."
                aria-invalid={showError("description") ? true : undefined}
              />
              {showError("description") && (
                <p className="mt-1 text-micro text-destructive">{errors.description}</p>
              )}
            </div>

            <details className="mt-4 rounded-lg border border-border p-3">
              <summary className="cursor-pointer text-sm font-medium">
                Add safety / access details
              </summary>
              <p className="mt-2 text-xs text-muted-foreground">
                Optional. Unknown answers stay unknown; the agent will ask for missing information.
              </p>
              <div className="mt-3 grid grid-cols-2 gap-3">
                {SAFETY_FIELDS.map(([field, label]) => (
                  <label key={field} className={labelClass}>
                    {label}
                    <select
                      className={fieldClass}
                      value={safety[field] ?? "UNKNOWN"}
                      onChange={(e) =>
                        setSafety({ ...safety, [field]: e.target.value as SafetyAnswer })
                      }
                    >
                      <option value="UNKNOWN">Unknown / not answered</option>
                      <option value="NO">No</option>
                      <option value="YES">Yes</option>
                    </select>
                  </label>
                ))}
              </div>
              <label className="mt-3 flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={hasAvailability}
                  onChange={(e) => setHasAvailability(e.target.checked)}
                />
                Tenant has confirmed an availability window
              </label>
              {hasAvailability && (
                <div className="mt-3 grid gap-3">
                  <label className={labelClass}>
                    Available from
                    <input
                      type="datetime-local"
                      className={fieldClass}
                      value={availableFrom}
                      onChange={(e) => setAvailableFrom(e.target.value)}
                    />
                  </label>
                  <label className={labelClass}>
                    Available until
                    <input
                      type="datetime-local"
                      className={fieldClass}
                      value={availableUntil}
                      onChange={(e) => setAvailableUntil(e.target.value)}
                    />
                  </label>
                  <p className="text-micro text-muted-foreground">
                    Times use your browser's local timezone.
                  </p>
                </div>
              )}
              {showError("availability") && (
                <p className="mt-2 text-xs text-destructive">{errors.availability}</p>
              )}
            </details>

            <div className="mt-5 flex items-center justify-end gap-2">
              <Dialog.Close asChild>
                <Button variant="ghost" size="sm" disabled={createTicket.isPending}>
                  Cancel
                </Button>
              </Dialog.Close>
              <Button type="submit" size="sm" disabled={createTicket.isPending}>
                {createTicket.isPending ? "Creating…" : "Create ticket"}
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

type OperatorIntakeCategory = "ROOFING" | "PLUMBING" | "ELECTRICAL" | "SCAFFOLDING" | "OTHER";
