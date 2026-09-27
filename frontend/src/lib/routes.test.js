import assert from "node:assert/strict";
import test from "node:test";
import { resolveRoute } from "./routes.js";

test("signed out /chat renders the landing page and remembers the path", () => {
  const decision = resolveRoute({ signedIn: false, path: "/chat", profileId: null });
  assert.equal(decision.screen, "landing");
  assert.equal(decision.remember, "/chat");
  assert.equal(decision.redirect, null);
});

test("signed in with no profile on /goals renders /profile", () => {
  const decision = resolveRoute({ signedIn: true, path: "/goals", profileId: null });
  assert.equal(decision.screen, "profile");
  assert.equal(decision.redirect, "/profile");
});

test("signed in with a profile on /advisory renders advisory", () => {
  const decision = resolveRoute({ signedIn: true, path: "/advisory", profileId: 4 });
  assert.equal(decision.screen, "advisory");
  assert.equal(decision.redirect, null);
});
