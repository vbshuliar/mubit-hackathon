import { expect, it } from "vitest";
import { presentationText } from "./presentation";

it("cleans only the known fixture markers for presentation", () => {
  expect(
    presentationText("SIMULATED CONTRACTOR REPORT: Fixture Roofers attended — simulated demo"),
  ).toBe("Roofers attended");
  expect(presentationText("Fixture Tenant at Fixture House (DEMO ONLY)")).toBe("Tenant at House");
  expect(
    presentationText(
      "SIMULATED_FIXTURE_DEMO:roof-scaffold-v1: resolve after simulated tenant confirmation.",
    ),
  ).toBe("resolve after tenant confirmation.");
  expect(presentationText("SIMULATED fixture report: fixture site remains secure.")).toBe(
    "site remains secure.",
  );
  expect(presentationText("Roof leak requiring scaffolding — simulated demo")).toBe(
    "Roof leak requiring scaffolding",
  );
  expect(presentationText("The agent is waiting for a simulated response.")).toBe(
    "The agent is waiting for a response.",
  );
  expect(presentationText("schedule simulated SCAFFOLD_INSTALL visit")).toBe(
    "schedule SCAFFOLD_INSTALL visit",
  );
  expect(presentationText("accept simulated SCAFFOLD_REMOVE completion evidence")).toBe(
    "accept SCAFFOLD_REMOVE completion evidence",
  );
  expect(presentationText("all simulated work complete")).toBe("all work complete");
  expect(presentationText("Roofers (fictional, SIMULATED)")).toBe("Roofers");
});

it("leaves normal application text unchanged", () => {
  expect(presentationText("Contractor report: Roofers attended at House")).toBe(
    "Contractor report: Roofers attended at House",
  );
});
