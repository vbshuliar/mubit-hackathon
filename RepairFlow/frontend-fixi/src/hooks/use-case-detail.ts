import { useQuery } from "@tanstack/react-query";
import { fetchCaseDetail } from "@/api/endpoints";
import type { CaseDetailResponse } from "@/api/types";
import { useAuthedCreds } from "@/lib/auth-context";

const POLL_INTERVAL_MS = 2000;

export function caseDetailQueryKey(caseId: string | null) {
  return ["case-detail", caseId] as const;
}

/** Always refresh the full snapshot: jobs and requests can change without a case version bump. */
export function useCaseDetail(caseId: string | null) {
  const creds = useAuthedCreds();
  const queryKey = caseDetailQueryKey(caseId);

  return useQuery<CaseDetailResponse>({
    queryKey,
    enabled: caseId !== null,
    refetchInterval: POLL_INTERVAL_MS,
    queryFn: async () => {
      if (!caseId) throw new Error("useCaseDetail called without a case id");
      const result = await fetchCaseDetail(creds, caseId);
      if (result.status !== 200) throw new Error(`failed to load case ${caseId}`);
      return result.body;
    },
  });
}
