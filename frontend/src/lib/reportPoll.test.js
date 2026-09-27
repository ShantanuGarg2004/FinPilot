import assert from "node:assert/strict";
import test from "node:test";
import { nextReportState } from "./reportPoll.js";

test("a queued job then a report with no active job leaves generating and shows the report", () => {
  const started = nextReportState(
    { phase: "idle", report: null, generation: 0 },
    { type: "enqueue" },
  );
  assert.equal(started.action, "poll");
  assert.equal(started.phase, "generating");

  const queued = nextReportState(started, {
    type: "snapshot",
    body: { job: { status: "queued" } },
  });
  assert.equal(queued.action, "poll");
  assert.equal(queued.generation, started.generation);

  const done = nextReportState(queued, {
    type: "snapshot",
    body: { ai_report: "Keep it in cash.", pdf_ready: true },
  });
  assert.equal(done.action, "stop");
  assert.equal(done.phase, "idle");
  assert.equal(done.error, null);
  assert.equal(done.report.ai_report, "Keep it in cash.");
});

test("a failed job keeps the older report and records the error", () => {
  const next = nextReportState(
    { phase: "generating", report: { ai_report: "Original advisory" }, generation: 1 },
    {
      type: "snapshot",
      body: { job: { status: "failed", error_code: "upstream_error" } },
    },
  );
  assert.equal(next.action, "stop");
  assert.equal(next.phase, "idle");
  assert.equal(next.report.ai_report, "Original advisory");
  assert.equal(next.error, "upstream_error");
});

test("a second enqueue while running does not reset the poll", () => {
  const first = nextReportState(
    { phase: "idle", report: { ai_report: "Original advisory" }, generation: 3 },
    { type: "enqueue" },
  );
  const second = nextReportState(first, { type: "enqueue" });
  assert.equal(first.action, "poll");
  assert.equal(second.action, "ignore");
  assert.equal(second.phase, "generating");
  assert.equal(second.generation, first.generation);
  assert.equal(second.report.ai_report, "Original advisory");
});

test("a timeout stops and keeps the report", () => {
  const next = nextReportState(
    { phase: "generating", report: { ai_report: "Original advisory" }, generation: 2 },
    { type: "timeout" },
  );
  assert.equal(next.action, "stop");
  assert.equal(next.error, "timeout");
  assert.equal(next.phase, "idle");
  assert.equal(next.report.ai_report, "Original advisory");
});
