import assert from "node:assert/strict";
import test from "node:test";
import {
  entryMatchesEpoch,
  makeHistoryState,
  pathForForeignEntry,
} from "./historySession.js";

test("a history entry matches only the epoch that created it", () => {
  const state = makeHistoryState("epoch-a", 4);
  assert.equal(entryMatchesEpoch(state, "epoch-a"), true);
  assert.equal(entryMatchesEpoch(state, "epoch-b"), false);
  assert.equal(entryMatchesEpoch(null, "epoch-a"), false);
  assert.equal(entryMatchesEpoch(state, ""), false);
});

test("a foreign entry signed out returns to the landing path", () => {
  assert.equal(pathForForeignEntry("", 12), "/");
});

test("a foreign entry signed in opens the current account home", () => {
  assert.equal(pathForForeignEntry("epoch-b", null), "/profile");
  assert.equal(pathForForeignEntry("epoch-b", 9), "/dashboard");
});
