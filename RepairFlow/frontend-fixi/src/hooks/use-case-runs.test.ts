import { expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({ fetch: vi.fn(), creds: { username: "test", password: "test" } }));
vi.mock("@tanstack/react-query", () => ({ useQuery: (options: unknown) => options }));
vi.mock("@/api/endpoints", () => ({ fetchCaseRuns: mocks.fetch }));
vi.mock("@/lib/auth-context", () => ({ useAuthedCreds: () => mocks.creds }));
import { useCaseRuns } from "./use-case-runs";
it("continues polling until and after a final decision arrives, independent of agent activity", async () => {
  const options = useCaseRuns("case") as unknown as {
    refetchInterval: number;
    queryFn: () => Promise<unknown>;
  };
  mocks.fetch
    .mockResolvedValueOnce({ items: [{ state: "RUNNING" }] })
    .mockResolvedValueOnce({ items: [{ state: "FAILED", error_code: "Invalid output" }] });
  expect(options.refetchInterval).toBe(4000);
  expect(await options.queryFn()).toEqual({ items: [{ state: "RUNNING" }] });
  expect(await options.queryFn()).toEqual({
    items: [{ state: "FAILED", error_code: "Invalid output" }],
  });
});
