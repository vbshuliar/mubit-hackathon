/** Display-only cleanup for the rehearsal workspace.
 *
 * This deliberately changes only known fixture markers. API payloads and
 * mutation bodies remain untouched, so presentation mode cannot alter
 * provenance, statuses, or the records submitted to the backend.
 */
export function presentationText(value: string): string {
  return value
    .replace(/FIXTURE-DEMO-ROOF/g, "ROOF")
    .replace(/\b(?:SIMULATED\s+)?fixture:\s*/gi, "")
    .replace(/\bFixture Roofers\b/g, "Roofers")
    .replace(/\bFixture Tenant\b/g, "Tenant")
    .replace(/\bFixture House\b/g, "House")
    .replace(/\bfixture site\b/gi, "site")
    .replace(/^\s*SIMULATED_FIXTURE_DEMO:[^:]+:\s*/i, "")
    .replace(/^\s*SIMULATED(?:\s+(?:(?:CONTRACTOR|FIXTURE)\s+)?REPORT)?\s*:\s*/i, "")
    .replace(/\s*[—-]\s*simulated demo\b/gi, "")
    .replace(/\s*\(fictional,\s*SIMULATED\)\s*$/i, "")
    .replace(/\bsimulated\s+/gi, "")
    .replace(/\s*\(?DEMO ONLY\)?\s*/gi, " ")
    .replace(/\s{2,}/g, " ")
    .trim();
}
