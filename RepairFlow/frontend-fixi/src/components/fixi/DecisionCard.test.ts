import { beforeEach, expect, it, vi } from "vitest";
import type { ReactElement, ReactNode } from "react";
import type { ActionRecord, CaseSnapshot } from "@/api/types";
const mocks = vi.hoisted(() => ({
  open: false,
  reason: "",
  setOpen: vi.fn(),
  focus: vi.fn(),
  setReason: vi.fn(),
  mutation: {
    mutateAsync: vi.fn(),
    reset: vi.fn(),
    isPending: false,
    isError: false,
    error: null as Error | null,
  },
}));
vi.mock("react", async (original) => ({
  ...(await original<typeof import("react")>()),
  useId: () => "rejection-reason",
  useRef: () => ({ current: { focus: mocks.focus } }),
  useState: (initial: unknown) =>
    typeof initial === "boolean" ? [mocks.open, mocks.setOpen] : [mocks.reason, mocks.setReason],
}));
vi.mock("@/hooks/use-case-actions", () => ({ useDecideApproval: () => mocks.mutation }));
import { DecisionCard } from "./DecisionCard";
type Element = ReactElement<Record<string, unknown>>;
function elements(node: ReactNode): Element[] {
  if (Array.isArray(node)) return node.flatMap(elements);
  if (!node || typeof node !== "object" || !("props" in node)) return [];
  const element = node as Element;
  return [element, ...elements(element.props["children"] as ReactNode)];
}
function row() {
  const action = {
    id: "action",
    state: "AWAITING_APPROVAL",
    payload_hash: "hash",
    proposal: {
      expected_case_version: 7,
      action: { kind: "APPLY_TRIAGE", risk: { gas: "UNKNOWN" }, scope: "Long scope ".repeat(20) },
      decision_summary: "Book specialist",
      evidence_refs: [],
    },
  } as unknown as ActionRecord;
  const tree = DecisionCard({
    caseId: "case",
    pendingActions: [action],
    snapshot: { case: { version: 8 } } as CaseSnapshot,
  });
  const child = elements(tree).find((e) => typeof e.type === "function" && "action" in e.props)!;
  return elements((child.type as (props: unknown) => ReactNode)(child.props));
}
function button(tree: Element[], text: string) {
  return tree.find((e) => e.type === "button" && e.props["children"] === text)!;
}
beforeEach(() => {
  vi.clearAllMocks();
  mocks.open = false;
  mocks.reason = "";
  mocks.mutation.isPending = false;
  mocks.mutation.isError = false;
  mocks.mutation.error = null;
  mocks.mutation.mutateAsync.mockResolvedValue({});
});
it("opens the in-page rejection dialog instead of a browser prompt", () => {
  (button(row(), "Reject").props["onClick"] as () => void)();
  expect(mocks.setOpen).toHaveBeenCalledWith(true);
  expect(mocks.mutation.mutateAsync).not.toHaveBeenCalled();
});
it("has a labelled required reason and blocks whitespace submission", () => {
  mocks.open = true;
  mocks.reason = "   ";
  const tree = row();
  expect(tree.find((e) => e.type === "textarea")?.props).toMatchObject({
    id: "rejection-reason",
    required: true,
  });
  expect(tree.find((e) => e.type === "label")?.props["htmlFor"]).toBe("rejection-reason");
  expect(button(tree, "Reject action").props["disabled"]).toBe(true);
  (tree.find((e) => e.type === "form")!.props["onSubmit"] as (event: unknown) => void)({
    preventDefault: vi.fn(),
  });
  expect(mocks.mutation.mutateAsync).not.toHaveBeenCalled();
});
it("submits trimmed rejection with current version and proposal payload hash", async () => {
  mocks.open = true;
  mocks.reason = "  Quote needs review.  ";
  (row().find((e) => e.type === "form")!.props["onSubmit"] as (event: unknown) => void)({
    preventDefault: vi.fn(),
  });
  await Promise.resolve();
  expect(mocks.mutation.mutateAsync).toHaveBeenCalledWith({
    actionId: "action",
    expectedCaseVersion: 8,
    approve: false,
    reason: "Quote needs review.",
    actionPayloadHash: "hash",
  });
  expect(mocks.setOpen).toHaveBeenCalledWith(false);
  expect(mocks.setReason).toHaveBeenCalledWith("");
});
it("cancel closes without rejecting", () => {
  (button(row(), "Cancel").props["onClick"] as () => void)();
  expect(mocks.setOpen).toHaveBeenCalledWith(false);
  expect(mocks.mutation.mutateAsync).not.toHaveBeenCalled();
});
it("preserves the reason when rejection fails", async () => {
  mocks.reason = "Needs a different contractor";
  mocks.mutation.mutateAsync.mockRejectedValueOnce(new Error("Conflict"));
  (row().find((e) => e.type === "form")!.props["onSubmit"] as (event: unknown) => void)({
    preventDefault: vi.fn(),
  });
  await Promise.resolve();
  expect(mocks.setReason).not.toHaveBeenCalled();
  expect(mocks.setOpen).not.toHaveBeenCalled();
});
it("blocks duplicate submission while a decision is pending", () => {
  mocks.reason = "Reason";
  mocks.mutation.isPending = true;
  const tree = row();
  expect(button(tree, "Rejecting…").props["disabled"]).toBe(true);
  (tree.find((e) => e.type === "form")!.props["onSubmit"] as (event: unknown) => void)({
    preventDefault: vi.fn(),
  });
  expect(mocks.mutation.mutateAsync).not.toHaveBeenCalled();
});

it("approval still uses the original proposal version", () => {
  (button(row(), "Approve").props["onClick"] as () => void)();
  expect(mocks.mutation.mutateAsync).toHaveBeenCalledWith(
    expect.objectContaining({ approve: true, expectedCaseVersion: 7 }),
  );
});

it("returns keyboard focus to Reject when the dialog closes", () => {
  const close = row().find((e) => typeof e.props["onCloseAutoFocus"] === "function")!;
  const preventDefault = vi.fn();
  (close.props["onCloseAutoFocus"] as (event: unknown) => void)({ preventDefault });
  expect(preventDefault).toHaveBeenCalled();
  expect(mocks.focus).toHaveBeenCalled();
});

it("exposes nested fields and long scope in the approval inspection", () => {
  const tree = row();
  const payload = tree.find((e) => e.type === "pre")?.props["children"] as string;
  expect(JSON.parse(payload)).toMatchObject({
    action: { risk: { gas: "UNKNOWN" }, scope: "Long scope ".repeat(20) },
    evidence_refs: [],
  });
});
