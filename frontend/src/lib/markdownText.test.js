import assert from "node:assert/strict";
import test from "node:test";
import { parseMarkdown } from "./markdownText.js";

test("a script tag in advisory text stays text", () => {
  const html = parseMarkdown("See <script>alert(1)</script> now");
  assert.equal(html.includes("<script"), false);
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
});

test("an image with an event handler stays text", () => {
  const html = parseMarkdown('<img src=x onerror="alert(1)">');
  assert.equal(html.includes("<img"), false);
  assert.match(html, /&lt;img src=x onerror="alert\(1\)"&gt;/);
});

test("a javascript link does not become a link", () => {
  const html = parseMarkdown("[click](javascript:alert(1))");
  assert.equal(html.includes("javascript:"), false);
  assert.equal(html.includes("<a"), false);
  assert.match(html, />click</);
});
