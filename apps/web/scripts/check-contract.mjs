// Fails when src/types/api.ts drifts from the backend OpenAPI schema (apps/web/openapi.json).
import { readFileSync } from "node:fs";

const spec = JSON.parse(readFileSync(new URL("../openapi.json", import.meta.url), "utf8"));
const types = readFileSync(new URL("../src/types/api.ts", import.meta.url), "utf8");

function listed(constName) {
  const m = new RegExp(`${constName} = \\[([\\s\\S]*?)\\] as const`).exec(types);
  if (!m) throw new Error(`${constName} not found in src/types/api.ts`);
  return [...m[1].matchAll(/"([^"]+)"/g)].map((x) => x[1]).sort();
}

const pairs = [
  ["EventOut", "EVENT_DTO_FIELDS"],
  ["ProfileOut", "PROFILE_DTO_FIELDS"],
];
let failed = false;
for (const [schemaName, constName] of pairs) {
  const actual = Object.keys(spec.components.schemas[schemaName].properties).sort();
  const expected = listed(constName);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    failed = true;
    console.error(`Contract drift in ${schemaName}:\n  openapi: ${actual}\n  types:   ${expected}`);
  }
}
if (failed) process.exit(1);
process.stdout.write("API contract check passed\n");
