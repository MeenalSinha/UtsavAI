import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { EVENT_DTO_FIELDS, PROFILE_DTO_FIELDS } from "@/types/api";

const spec = JSON.parse(readFileSync(resolve(process.cwd(), "openapi.json"), "utf8"));

describe("OpenAPI contract", () => {
  it("TypeScript DTO fields match the generated backend schema", () => {
    expect(Object.keys(spec.components.schemas.EventOut.properties).sort()).toEqual([...EVENT_DTO_FIELDS].sort());
    expect(Object.keys(spec.components.schemas.ProfileOut.properties).sort()).toEqual([...PROFILE_DTO_FIELDS].sort());
  });

  it("exposes the Phase 0 endpoints", () => {
    expect(Object.keys(spec.paths["/api/v1/events"]).sort()).toEqual(["get", "post"]);
    expect(Object.keys(spec.paths["/api/v1/events/{event_id}"]).sort()).toEqual(["delete", "get", "patch"]);
  });
});
