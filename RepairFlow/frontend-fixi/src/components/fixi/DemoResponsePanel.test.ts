import { beforeEach, expect, it, vi } from "vitest";
import type { ReactElement, ReactNode } from "react";
import type { CaseSnapshot } from "@/api/types";
const mocks = vi.hoisted(() => ({
  states: [] as unknown[],
  cursor: 0,
  mutation: { mutateAsync: vi.fn(), reset: vi.fn(), isPending: false, isError: false },
  ref: { current: null as unknown },
}));
vi.mock("react", async (original) => ({
  ...(await original<typeof import("react")>()),
  useRef: () => mocks.ref,
  useState: (initial: unknown) => {
    const i = mocks.cursor++;
    if (!(i in mocks.states)) mocks.states[i] = initial;
    return [
      mocks.states[i],
      (value: unknown) => {
        mocks.states[i] = value;
      },
    ];
  },
}));
vi.mock("@/hooks/use-demo-input", () => ({ useDemoInput: () => mocks.mutation }));
import { DemoResponsePanel } from "./DemoResponsePanel";
type Element = ReactElement<Record<string, unknown>>;
function elements(node: ReactNode): Element[] {
  if (Array.isArray(node)) return node.flatMap(elements);
  if (!node || typeof node !== "object" || !("props" in node)) return [];
  const element = node as Element;
  return [element, ...elements(element.props["children"] as ReactNode)];
}
const snapshot = (visits: string[] = []) =>
  ({
    case: { id: "case", status: "ACTIVE", version: 1 },
    appointments: visits.map((id) => ({
      id,
      work_order_id: "work",
      status: "CONFIRMED",
      start_at: "2026-10-25T09:00:00Z",
      end_at: "2026-10-25T12:00:00Z",
    })),
    work_orders: [{ id: "work", status: "SCHEDULED", trade: "PLUMBING" }],
    communications: [],
    latest_reports: [],
    agent_active: false,
  }) as unknown as CaseSnapshot;
function render(s: CaseSnapshot) {
  mocks.cursor = 0;
  return elements(DemoResponsePanel({ snapshot: s }));
}
function edit(tree: Element[]) {
  (tree.find((e) => e.type === "form")!.props["onChangeCapture"] as () => void)();
  (tree.find((e) => e.type === "textarea")!.props["onChange"] as (e: unknown) => void)({
    target: { value: "Visit completed" },
  });
}
beforeEach(() => {
  mocks.states = [];
  mocks.ref.current = null;
  vi.clearAllMocks();
});
it("pins response kind while a draft is edited across polling", () => {
  edit(render(snapshot()));
  const tree = render(snapshot(["new"]));
  expect(tree.find((e) => e.type === "select")?.props["value"]).toBe("TENANT_REPLY");
});
it("never moves an edited visit report to a replacement appointment", () => {
  edit(render(snapshot(["old"])));
  const tree = render(snapshot(["new"]));
  expect(tree.filter((e) => e.type === "select")[1]?.props["value"]).toBe("");
  expect(tree.find((e) => e.props["type"] === "submit")?.props["disabled"]).toBe(true);
});
it("blocks sending when the requested person or question has changed", () => {
  const s = snapshot();
  s.communications = [
    { id: "old", tenant_id: "tenant", state: "REQUESTED", purpose: "INTAKE", transcript: [] },
  ] as unknown as CaseSnapshot["communications"];
  edit(render(s));
  const next = { ...s, communications: [{ ...s.communications[0], id: "new" }] } as CaseSnapshot;
  const tree = render(next);
  expect(tree.find((e) => e.props["type"] === "submit")?.props["disabled"]).toBe(true);
  expect(tree.some((e) => e.props["role"] === "alert")).toBe(true);
});
it("blocks form submission during active agent work", () => {
  edit(render(snapshot()));
  const tree = render({ ...snapshot(), agent_active: true });
  (tree.find((e) => e.type === "form")!.props["onSubmit"] as (e: unknown) => void)({
    preventDefault: vi.fn(),
  });
  expect(mocks.mutation.mutateAsync).not.toHaveBeenCalled();
});

it("keeps a contractor report request open when the report is still missing", async () => {
  const s = snapshot(["visit"]);
  s.communications = [
    {
      id: "report-request",
      tenant_id: null,
      state: "REQUESTED",
      purpose: "CONTRACTOR",
      transcript: [],
    },
  ] as unknown as CaseSnapshot["communications"];
  let tree = render(s);
  (tree.find((e) => e.type === "select")!.props["onChange"] as (e: unknown) => void)({
    target: { value: "ATTENDANCE_OUTCOME" },
  });
  edit(render(s));
  tree = render(s);
  (tree.find((e) => e.type === "form")!.props["onSubmit"] as (e: unknown) => void)({
    preventDefault: vi.fn(),
  });
  await Promise.resolve();
  expect(mocks.mutation.mutateAsync).toHaveBeenCalledWith(
    expect.objectContaining({ kind: "ATTENDANCE_OUTCOME", attendance_outcome: "AWAITING_REPORT" }),
  );
  expect(mocks.mutation.mutateAsync.mock.calls[0]![0]).not.toHaveProperty(
    "response_to_communication_id",
  );
});
it("does not mark an availability question answered without confirmed windows", async () => {
  const s = snapshot();
  s.communications = [
    {
      id: "availability",
      tenant_id: "tenant",
      state: "REQUESTED",
      purpose: "AVAILABILITY",
      transcript: [],
    },
  ] as unknown as CaseSnapshot["communications"];
  edit(render(s));
  const tree = render(s);
  (tree.find((e) => e.type === "form")!.props["onSubmit"] as (e: unknown) => void)({
    preventDefault: vi.fn(),
  });
  await Promise.resolve();
  expect(mocks.mutation.mutateAsync).toHaveBeenCalled();
  expect(mocks.mutation.mutateAsync.mock.calls[0]![0]).not.toHaveProperty(
    "response_to_communication_id",
  );
});

function accessCheckbox(tree: Element[], text: string) {
  const label = tree.find(
    (e) => e.type === "label" && JSON.stringify(e.props["children"]).includes(text),
  )!;
  return elements(label).find((e) => e.type === "input")!;
}
function toggle(tree: Element[], label: string, checked: boolean) {
  (accessCheckbox(tree, label).props["onChange"] as (e: unknown) => void)({ target: { checked } });
}
it("sends explicit access withdrawal without inventing replacement windows", async () => {
  const s = snapshot();
  edit(render(s));
  toggle(render(s), "Withdraw all previous access times", true);
  const tree = render(s);
  (tree.find((e) => e.type === "form")!.props["onSubmit"] as (e: unknown) => void)({
    preventDefault: vi.fn(),
  });
  await Promise.resolve();
  expect(mocks.mutation.mutateAsync).toHaveBeenCalledWith(
    expect.objectContaining({ kind: "TENANT_REPLY", withdraw_availability: true }),
  );
  expect(mocks.mutation.mutateAsync.mock.calls[0]![0]).not.toHaveProperty("availability");
});
it("new access times and withdrawal are mutually exclusive", () => {
  const s = snapshot();
  toggle(render(s), "Provide new tenant-confirmed access times", true);
  toggle(render(s), "Withdraw all previous access times", true);
  expect(
    accessCheckbox(render(s), "Provide new tenant-confirmed access times").props["checked"],
  ).toBe(false);
  toggle(render(s), "Provide new tenant-confirmed access times", true);
  expect(accessCheckbox(render(s), "Withdraw all previous access times").props["checked"]).toBe(
    false,
  );
});
it("does not expose access withdrawal for contractor visit reports", () => {
  const tree = render(snapshot(["visit"]));
  expect(
    tree
      .filter((e) => e.type === "label")
      .some((e) =>
        JSON.stringify(e.props["children"]).includes("Withdraw all previous access times"),
      ),
  ).toBe(false);
});

function operatorDraft(s: CaseSnapshot) {
  const tree = render(s);
  (tree.find((e) => e.type === "select")!.props["onChange"] as (e: unknown) => void)({
    target: { value: "OPERATOR_UPDATE" },
  });
  edit(render(s));
  return render(s);
}
const concernSnapshot = () =>
  ({
    ...snapshot(),
    issue: {
      unresolved_concerns: [
        "Scaffold inspection certificate missing",
        "tenant reports issue still unresolved",
      ],
    },
  }) as CaseSnapshot;
it("offers only operator-addressable concerns and selects none automatically", () => {
  const s = concernSnapshot();
  expect(render(s).some((e) => e.type === "fieldset")).toBe(false);
  const tree = operatorDraft(s);
  expect(accessCheckbox(tree, "Scaffold inspection certificate missing").props["checked"]).toBe(
    false,
  );
  expect(
    tree
      .filter((e) => e.type === "label")
      .some((e) =>
        JSON.stringify(e.props["children"]).includes("tenant reports issue still unresolved"),
      ),
  ).toBe(false);
});
it("submits only explicitly selected existing concerns with operator explanation", async () => {
  const s = concernSnapshot();
  toggle(operatorDraft(s), "Scaffold inspection certificate missing", true);
  const tree = render(s);
  (tree.find((e) => e.type === "form")!.props["onSubmit"] as (e: unknown) => void)({
    preventDefault: vi.fn(),
  });
  await Promise.resolve();
  expect(mocks.mutation.mutateAsync).toHaveBeenCalledWith(
    expect.objectContaining({
      kind: "OPERATOR_UPDATE",
      resolved_concerns: ["Scaffold inspection certificate missing"],
      text: "Visit completed",
    }),
  );
  expect(
    accessCheckbox(operatorDraft(s), "Scaffold inspection certificate missing").props["checked"],
  ).toBe(false);
});
it("preserves addressed-concern selections after a failed save", async () => {
  const s = concernSnapshot();
  toggle(operatorDraft(s), "Scaffold inspection certificate missing", true);
  mocks.mutation.mutateAsync.mockRejectedValueOnce(new Error("Network unavailable"));
  const tree = render(s);
  (tree.find((e) => e.type === "form")!.props["onSubmit"] as (e: unknown) => void)({
    preventDefault: vi.fn(),
  });
  await Promise.resolve();
  expect(
    accessCheckbox(render(s), "Scaffold inspection certificate missing").props["checked"],
  ).toBe(true);
});
it("blocks a stale concern rather than silently changing the operator's selection", () => {
  const s = concernSnapshot();
  toggle(operatorDraft(s), "Scaffold inspection certificate missing", true);
  const tree = render({ ...s, issue: { ...s.issue, unresolved_concerns: [] } });
  expect(tree.find((e) => e.props["type"] === "submit")?.props["disabled"]).toBe(true);
});
