import { createFileRoute } from "@tanstack/react-router";
import { ProductPreview } from "@/components/preview/ProductPreview";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Fixi — From reported to resolved." },
      {
        name: "description",
        content:
          "Fixi coordinates the next step across tenants, contractors and approvals—keeping the repair, its blockers and its decisions in view.",
      },
    ],
  }),
  component: ProductPreview,
});
