import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { buildComplaint } from "./complaint.ts";

test("draft contains the details the user typed", () => {
  const out = buildComplaint({ date: "2026-10-06", caseSummary: "I paid money.", amount: "₹1,500", message: "Pay fee now" });
  assert.match(out, /06\/10\/2026/);
  assert.match(out, /Rs 1500/);
  assert.match(out, /Pay fee now/);
  assert.match(out, /I paid money\./);
});

test("optional fields fall back to placeholders", () => {
  const out = buildComplaint({ date: "", caseSummary: "x", amount: "", message: "  " });
  assert.match(out, /\[date\]/);
  assert.match(out, /\[amount, or none\]/);
  assert.doesNotMatch(out, /Message I received/);
});

test("complaint code makes no network request and keeps nothing", () => {
  const dir = new URL("../components/", import.meta.url);
  const sources = [
    readFileSync(new URL("./complaint.ts", import.meta.url), "utf8"),
    readFileSync(new URL("../components/ComplaintHelper.tsx", import.meta.url), "utf8"),
    readFileSync(new URL("../components/EmergencyHelp.tsx", import.meta.url), "utf8"),
  ].join("\n");
  assert.ok(readdirSync(dir).includes("ComplaintHelper.tsx"));
  for (const banned of ["fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "localStorage", "sessionStorage", "indexedDB", "console.", "/lib/api", "from \"../lib/api\""]) {
    assert.ok(!sources.includes(banned), `found forbidden "${banned}"`);
  }
});
