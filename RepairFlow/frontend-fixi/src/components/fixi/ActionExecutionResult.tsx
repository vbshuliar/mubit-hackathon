import type { OrchestrationRun } from "@/api/types";
import { executionOutcome } from "@/lib/action-execution";
import { cn } from "@/lib/utils";
export function ActionExecutionResult({ run }: { run: OrchestrationRun }) {
  const result = executionOutcome(run);
  return (
    <div
      role={result.failed || result.uncertain ? "alert" : "status"}
      className={cn(
        "rounded-lg border p-3 text-sm",
        result.failed || result.uncertain
          ? "border-destructive/30 bg-destructive/5 text-destructive"
          : "border-border bg-muted/30",
      )}
    >
      <p className="font-semibold">{result.label}</p>
      <p className="mt-1 text-xs">{result.detail}</p>
    </div>
  );
}
