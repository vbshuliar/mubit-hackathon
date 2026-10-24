import { expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({ fetch: vi.fn(), creds: { username: "test", password: "test" } }));
vi.mock("@tanstack/react-query", () => ({ useQuery: (options: unknown) => options }));
vi.mock("@/api/endpoints", () => ({ fetchCaseDetail: mocks.fetch }));
vi.mock("@/lib/auth-context", () => ({ useAuthedCreds: () => mocks.creds }));
import { useCaseDetail } from "./use-case-detail";
it("refreshes agent/request state without a known-version cache even at the same case version", async () => {
  const before = { snapshot: { case: { version: 1 }, agent_active: true } };
  const after = {
    snapshot: {
      case: { version: 1 },
      agent_active: false,
      communications: [{ state: "REQUESTED" }],
    },
  };
  mocks.fetch
    .mockResolvedValueOnce({ status: 200, body: before })
    .mockResolvedValueOnce({ status: 200, body: after });
  const options = useCaseDetail("case") as unknown as { queryFn: () => Promise<unknown> };
  expect(await options.queryFn()).toEqual(before);
  expect(await options.queryFn()).toEqual(after);
  expect(mocks.fetch).toHaveBeenNthCalledWith(1, mocks.creds, "case");
  expect(mocks.fetch).toHaveBeenNthCalledWith(2, mocks.creds, "case");
});
