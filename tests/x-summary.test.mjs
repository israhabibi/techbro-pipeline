import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import {
  chooseAuthMode,
  classifyTechbro,
  filterTechbroPosts,
  localSummary,
  reportingWindow,
  parseArgs,
  readCredentials,
  xRequest,
} from "../src/x-summary.mjs";

test("reportingWindow starts at midnight yesterday in Jakarta", () => {
  const window = reportingWindow(
    new Date("2026-10-04T12:30:00.000Z"),
    "Asia/Jakarta",
  );
  assert.equal(window.start.toISOString(), "2026-10-02T17:00:00.000Z");
  assert.equal(window.end.toISOString(), "2026-10-04T12:30:00.000Z");
});

test("reportingWindow crosses year boundary in Jakarta", () => {
  const window = reportingWindow(new Date("2026-01-01T01:00:00Z"));
  assert.equal(window.start.toISOString(), "2025-12-30T17:00:00.000Z");
});

test("argument parsing rejects unsupported options and values", () => {
  assert.throws(() => parseArgs(["--sentences", "4"]));
  assert.throws(() => parseArgs(["--auth", "unknown"]));
  assert.throws(() => parseArgs(["--source", "unknown"]));
  assert.throws(() => parseArgs(["--unknown"]));
  assert.equal(parseArgs(["--no-ai"]).useAi, false);
});

test("invalid credentials JSON never echoes its contents", async () => {
  const directory = await mkdtemp(path.join(tmpdir(), "techbro-test-"));
  try {
    const filename = path.join(directory, "fake-creds.json");
    await writeFile(filename, "fake-private-cookie { broken");
    await assert.rejects(readCredentials(filename), (error) => {
      assert.doesNotMatch(error.message, /fake-private-cookie/);
      return true;
    });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("X request authenticates, sets a timeout, and reports denied access", async (t) => {
  const original = globalThis.fetch;
  t.after(() => {
    globalThis.fetch = original;
  });
  globalThis.fetch = async (url, options) => {
    assert.equal(options.headers.Authorization, "Bearer fake-test-token");
    assert.ok(options.signal instanceof AbortSignal);
    return new Response(JSON.stringify({ detail: "denied" }), { status: 401 });
  };
  await assert.rejects(
    xRequest("https://example.test", "fake-test-token"),
    /OAuth/,
  );
});

test("localSummary creates one three-sentence point per short input", () => {
  const posts = [
    {
      created_at: "2026-10-04T01:00:00.000Z",
      text: "Mencoba agent baru untuk otomasi deployment.",
      public_metrics: { like_count: 2, retweet_count: 1, reply_count: 0 },
    },
    {
      created_at: "2026-10-03T03:00:00.000Z",
      text: "Catatan tentang keamanan token API dan secrets.",
      public_metrics: { like_count: 4, retweet_count: 0, reply_count: 1 },
    },
  ];
  const result = localSummary(posts, 3, "Asia/Jakarta");
  const points = result.split("\n\n");
  assert.equal(points.length, 2);
  assert.match(points[0], /^1\. Pokok bahasan:/);
  assert.match(points[0], /Kata atau tema yang paling menonjol/);
  assert.match(points[0], /Gabungan 1 tweet ini memperoleh/);
  assert.match(points[1], /^2\. Pokok bahasan:/);
});

test("localSummary reports an empty period", () => {
  assert.equal(localSummary([]), "Tidak ada tweet pada rentang waktu ini.");
});

test("classifyTechbro includes technology topics and jokes from technology accounts", () => {
  assert.equal(
    classifyTechbro({
      text: "Belajar Kubernetes untuk deployment baru",
      author: { name: "Rina", username: "rina", description: "" },
    }),
    "topik teknologi",
  );
  assert.equal(
    classifyTechbro({
      text: "Meeting-nya bisa jadi email wkwk",
      author: {
        name: "Dimas",
        username: "dimasdev",
        description: "Software engineer",
      },
    }),
    "candaan akun teknologi",
  );
});

test("filterTechbro excludes unrelated general posts", () => {
  const posts = [
    {
      id: "1",
      text: "Cuaca hari ini cerah",
      author: { description: "Traveler" },
    },
    {
      id: "2",
      text: "API baru ini lebih cepat",
      author: { description: "Writer" },
    },
  ];
  const result = filterTechbroPosts(posts);
  assert.deepEqual(
    result.map((post) => post.id),
    ["2"],
  );
  assert.equal(result[0].techbro_reason, "topik teknologi");
});

test("chooseAuthMode prefers session cookies in automatic mode", () => {
  assert.equal(
    chooseAuthMode(
      { auth: "auto" },
      { hasSessionCookies: true, accessToken: "api-token" },
    ),
    "cookies",
  );
  assert.equal(
    chooseAuthMode(
      { auth: "auto" },
      { hasSessionCookies: false, accessToken: "api-token" },
    ),
    "api",
  );
});
