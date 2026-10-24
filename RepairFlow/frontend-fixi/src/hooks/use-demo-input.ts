import { useMutation, useQueryClient } from "@tanstack/react-query";
import { request } from "@/api/client";
import { useAuthedCreds } from "@/lib/auth-context";
import type { SafetyAnswers } from "@/api/types";
import type { DemoInputKind } from "@/lib/demo-response";
export interface DemoInput {
  response_to_communication_id?: string;
  input_id: string;
  expected_case_version: number;
  attendance_outcome?: "NO_ACCESS" | "NO_SHOW" | "AWAITING_REPORT";
  kind: DemoInputKind;
  text: string;
  appointment_id?: string;
  safety_answers?: SafetyAnswers;
  withdraw_availability?: boolean;
  resolved_concerns?: string[];
  availability?: {
    start_at: string;
    end_at: string;
    timezone: string;
    spoken_text: string;
    confirmed_by_speaker: boolean;
  }[];
  confirms_resolved?: boolean;
}
export function useDemoInput(caseId: string) {
  const creds = useAuthedCreds();
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: DemoInput) =>
      request(creds, `/api/v1/cases/${caseId}/demo-inputs`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onError: () => {
      void client.invalidateQueries();
    },
    onSuccess: () => {
      void client.invalidateQueries();
    },
  });
}
