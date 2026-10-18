/** Explicit fault-injection host/HTTP fixtures. Not a real model or native graph run.
 * Exercises the actual plugin factory/hooks, including local files and Git.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { mkdtemp, mkdir, writeFile, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn, execFileSync } from "node:child_process";
import { performance } from "node:perf_hooks";
import { ChronosGraph } from "../src/bridge.ts";
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
async function fixture() {
  const directory = await mkdtemp(join(tmpdir(), "chronos-hook-fault-"));
  const git = (...a: string[]) =>
    execFileSync("git", ["-C", directory, ...a], { encoding: "utf8" }).trim();
  git("init", "-q");
  await writeFile(join(directory, "source.py"), "def value(): return 1\n");
  git("add", ".");
  git(
    "-c",
    "user.name=Fault fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-qm",
    "owned fault fixture",
  );
  const revision = git("rev-parse", "HEAD");
  await mkdir(join(directory, ".chronosgraph-local"));
  await writeFile(
    join(directory, ".git/info/exclude"),
    ".chronosgraph-local/\n",
  );
  const state = {
    eventStatus: 200,
    eventDelay: 0,
    packStatus: 200,
    requests: [] as any[],
    messages: new Map<string, any>(),
    logs: [] as string[],
  };
  const server = createServer(async (req, res) => {
    let body = "";
    for await (const c of req) body += c;
    const value = body ? JSON.parse(body) : undefined;
    if (req.url?.endsWith("/events")) {
      state.requests.push(value);
      await sleep(state.eventDelay);
      res.writeHead(state.eventStatus, { "content-type": "application/json" });
      res.end(
        JSON.stringify(
          state.eventStatus === 200
            ? { accepted: true }
            : { detail: "injected delivery failure" },
        ),
      );
    } else if (req.url?.endsWith("/runs")) {
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify({ id: "run_" + "e".repeat(32) }));
    } else {
      res.writeHead(state.packStatus, { "content-type": "application/json" });
      res.end(
        JSON.stringify(
          state.packStatus === 200
            ? {
                id: "pack_" + "d".repeat(32),
                manifest: { source_pins: [{ path: "source.py" }] },
              }
            : { detail: "stale pack" },
        ),
      );
    }
  });
  await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
  const address = server.address() as { port: number };
  const binding = {
    api_url: `http://127.0.0.1:${address.port}`,
    tenant_graph: "repo_fault",
    expected_revision: revision,
    task_id: "task_" + "b".repeat(32),
    plan_id: "plan_" + "c".repeat(32),
    pack_id: "pack_" + "d".repeat(32),
  };
  await writeFile(
    join(directory, ".chronosgraph-local/binding.json"),
    JSON.stringify(binding),
  );
  const input = {
    directory,
    client: {
      app: {
        log: async ({ body }: any) => {
          state.logs.push(body.message);
        },
      },
      session: {
        message: async ({ path }: any) => ({
          data: state.messages.get(path.messageID),
          error: undefined,
        }),
        messages: async () => ({ data: [...state.messages.values()] }),
      },
    },
  } as any;
  const hooks: any[] = [];
  return {
    directory,
    state,
    binding,
    async plugin() {
      const h = await ChronosGraph(input, {});
      hooks.push(h);
      return h;
    },
    output(id = "msg_first") {
      return { message: { id }, parts: [] as any[] };
    },
    async stored() {
      return JSON.parse(
        await readFile(
          join(directory, ".chronosgraph-local/telemetry-state.json"),
          "utf8",
        ),
      );
    },
    async close() {
      for (const h of hooks) await h.dispose?.();
      server.closeAllConnections();
      await new Promise<void>((r) => server.close(() => r()));
      await rm(directory, { recursive: true, force: true });
    },
  };
}

test("A: receipt upload failure after pack fetch must not abort the first context-bearing turn", async () => {
  const f = await fixture();
  try {
    f.state.eventStatus = 503;
    const h: any = await f.plugin();
    const out = f.output();
    await assert.doesNotReject(() =>
      h["chat.message"]({ sessionID: "ses_fault" }, out),
    );
    assert.equal(
      out.parts.filter((p: any) => p.type === "text" && p.synthetic).length,
      1,
    );
    await sleep(30);
    const stored = await f.stored();
    assert.ok(stored.runs.ses_fault.queue.length > 0);
  } finally {
    await f.close();
  }
});
test("B: slow telemetry must not be on the ordinary tool critical path (250ms fault-test budget)", async () => {
  const f = await fixture();
  try {
    const h: any = await f.plugin();
    await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
    f.state.eventDelay = 1200;
    const start = performance.now();
    await h["tool.execute.before"](
      { sessionID: "ses_fault", tool: "read", callID: "call_fault" },
      { args: { filePath: "source.py" } },
    );
    const elapsed = performance.now() - start;
    console.log("FAULT_HOOK_OVERHEAD_MS", elapsed);
    assert.ok(elapsed < 250, `${elapsed}ms exceeds 250ms`);
  } finally {
    await f.close();
  }
});
test("B: two plugin writers cannot mutate the same project state concurrently", async () => {
  const f = await fixture();
  try {
    await f.plugin();
    await assert.rejects(() => f.plugin(), /writer|lock|owned/i);
  } finally {
    await f.close();
  }
});

async function eventually(check: () => Promise<boolean>, timeout = 4000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (await check()) return;
    await sleep(25);
  }
  assert.fail("Timed out waiting for durable state");
}
test("A: same-message retry is duplicate-free; later turn skips only after SDK persistence evidence", async () => {
  const f = await fixture();
  try {
    const h: any = await f.plugin(),
      out = f.output();
    await h["chat.message"]({ sessionID: "ses_fault" }, out);
    await h["chat.message"]({ sessionID: "ses_fault" }, out);
    assert.equal(out.parts.length, 1);
    const stored = (await f.stored()).runs.ses_fault;
    assert.equal(stored.delivery.status, "INJECTED_UNCONFIRMED");
    f.state.messages.set(out.message.id, {
      info: out.message,
      parts: out.parts,
    });
    const later = f.output("msg_later");
    await h["chat.message"]({ sessionID: "ses_fault" }, later);
    assert.equal(later.parts.length, 0);
    assert.equal(
      (await f.stored()).runs.ses_fault.delivery.status,
      "HOST_PART_OBSERVED",
    );
  } finally {
    await f.close();
  }
});
test("A: restart without host confirmation reinjects; persisted message reconciles on next restart", async () => {
  const f = await fixture();
  try {
    let h: any = await f.plugin();
    const out = f.output();
    await h["chat.message"]({ sessionID: "ses_fault" }, out);
    await h.dispose();
    await sleep(40);
    h = await f.plugin();
    const retry = f.output();
    await h["chat.message"]({ sessionID: "ses_fault" }, retry);
    assert.equal(retry.parts.length, 1);
    assert.equal(retry.parts[0].id, out.parts[0].id);
    f.state.messages.set(out.message.id, {
      info: out.message,
      parts: retry.parts,
    });
    await h.dispose();
    await sleep(40);
    h = await f.plugin();
    const later = f.output("msg_later");
    await h["chat.message"]({ sessionID: "ses_fault" }, later);
    assert.equal(later.parts.length, 0);
  } finally {
    await f.close();
  }
});
test("A: stale pack refuses chat and managed proposal; compaction is bounded per output", async () => {
  const f = await fixture();
  try {
    const h: any = await f.plugin();
    await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
    const out = { context: [] as string[] };
    await h["experimental.session.compacting"]({ sessionID: "ses_fault" }, out);
    await h["experimental.session.compacting"]({ sessionID: "ses_fault" }, out);
    assert.equal(out.context.length, 1);
    f.state.packStatus = 409;
    f.state.eventStatus = 503;
    await assert.rejects(
      () =>
        h["chat.message"]({ sessionID: "ses_fault" }, f.output("msg_stale")),
      /409/,
    );
    await assert.rejects(
      () =>
        h["tool.execute.before"](
          {
            sessionID: "ses_fault",
            tool: "chronosgraph_propose_change_for_approval",
            callID: "stale",
          },
          { args: {} },
        ),
      /409/,
    );
  } finally {
    await f.close();
  }
});
test("B: outage queue survives restart and eventually drains without changing event identity", async () => {
  const f = await fixture();
  try {
    f.state.eventStatus = 503;
    let h: any = await f.plugin();
    await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
    await h["tool.execute.before"](
      { sessionID: "ses_fault", tool: "read", callID: "queued" },
      { args: {} },
    );
    await eventually(async () => f.state.requests.length > 0);
    await h.dispose();
    const prior = (await f.stored()).runs.ses_fault.queue;
    assert.ok(prior.length >= 2);
    f.state.eventStatus = 200;
    await sleep(40);
    h = await f.plugin();
    await eventually(
      async () => (await f.stored()).runs.ses_fault.queue.length === 0,
    );
    assert.ok(
      prior.every((e: any) =>
        f.state.requests.some(
          (x) =>
            x.event_id === e.event_id && x.payload_digest === e.payload_digest,
        ),
      ),
    );
  } finally {
    await f.close();
  }
});
test("B: permanent rejected head is quarantined, later events drain; stale binding stops visibly", async () => {
  const f = await fixture();
  try {
    f.state.eventStatus = 422;
    const h: any = await f.plugin();
    await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
    await eventually(
      async () =>
        (await f.stored()).runs.ses_fault.transport.blocked.length === 1,
    );
    const rejected = (await f.stored()).runs.ses_fault.transport.blocked[0];
    assert.equal(rejected.envelope.kind, "CONTEXT_INJECTED");
    f.state.eventStatus = 200;
    await h["tool.execute.before"](
      { sessionID: "ses_fault", tool: "read", callID: "after_reject" },
      { args: {} },
    );
    await eventually(
      async () => (await f.stored()).runs.ses_fault.queue.length === 0,
    );
    assert.equal((await f.stored()).runs.ses_fault.transport.blocked.length, 1);
    f.state.eventStatus = 403;
    await h["tool.execute.before"](
      { sessionID: "ses_fault", tool: "read", callID: "stale_binding" },
      { args: {} },
    );
    await eventually(
      async () =>
        (await f.stored()).runs.ses_fault.transport.reconciliation_required,
    );
    assert.equal((await f.stored()).runs.ses_fault.queue.length, 1);
  } finally {
    await f.close();
  }
});
test("B: retention exhaustion preserves originals, explicitly counts unobserved; dispose is bounded", async () => {
  const f = await fixture();
  try {
    f.state.eventDelay = 1200;
    f.state.eventStatus = 503;
    const h: any = await f.plugin();
    await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
    for (let i = 0; i < 254; i++)
      await h["tool.execute.before"](
        { sessionID: "ses_fault", tool: "read", callID: `retention_${i}` },
        { args: {} },
      );
    const r = (await f.stored()).runs.ses_fault;
    assert.equal(r.queue.length, 250);
    assert.equal(r.transport.unobserved_count, 5);
    assert.equal(r.transport.saturated, true);
    assert.equal(r.queue[0].kind, "CONTEXT_INJECTED");
    const start = performance.now();
    await h.dispose();
    assert.ok(performance.now() - start < 750);
  } finally {
    await f.close();
  }
});

test("B: kernel lock excludes another process and releases after abrupt process death", async () => {
  const f = await fixture();
  let child: ReturnType<typeof spawn> | undefined;
  try {
    const moduleUrl = new URL("../src/bridge.ts", import.meta.url).href;
    child = spawn(
      process.execPath,
      [
        "--experimental-strip-types",
        "--input-type=module",
        "-e",
        `import {ChronosGraph} from ${JSON.stringify(moduleUrl)};const h=await ChronosGraph({directory:${JSON.stringify(f.directory)},client:{app:{log:async()=>{}},session:{message:async()=>({data:undefined})}}},{});await h['chat.message']({sessionID:'ses_fault'},{message:{id:'msg_child'},parts:[]});console.log('READY');setInterval(()=>{},1000);`,
      ],
      { stdio: ["ignore", "pipe", "pipe"] },
    );
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(
        () => reject(Error("child startup timeout")),
        5000,
      );
      child!.once("exit", (code) => {
        clearTimeout(timeout);
        reject(Error("child exited " + code));
      });
      child!.stdout!.on("data", (d) => {
        if (String(d).includes("READY")) {
          clearTimeout(timeout);
          resolve();
        }
      });
    });
    await assert.rejects(() => f.plugin(), /writer|lock|owned/i);
    const exited = new Promise((r) => child!.once("exit", r));
    child.kill("SIGKILL");
    await exited;
    await sleep(70);
    const h: any = await f.plugin();
    const output = f.output("msg_after_crash");
    await h["chat.message"]({ sessionID: "ses_fault" }, output);
    assert.equal(output.parts.length, 1);
    assert.equal(
      (await f.stored()).runs.ses_fault.delivery.message_id,
      "msg_after_crash",
    );
  } finally {
    child?.kill("SIGKILL");
    await f.close();
  }
});

test("E: completed steps replay stably; message costs reconcile without duplicating step usage", async () => {
  const f = await fixture();
  try {
    f.state.eventStatus = 503;
    const h: any = await f.plugin();
    await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
    const m = {
      id: "msg_assistant",
      sessionID: "ses_fault",
      role: "assistant",
      providerID: "opencode",
      modelID: "deepseek-v4.1-flash-free",
      time: { created: 1, completed: 3 },
      cost: 0,
      tokens: {
        input: 20,
        output: 4,
        reasoning: 1,
        cache: { read: 3, write: 0 },
      },
    };
    const step = (id: string, input: number) => ({
      id,
      sessionID: "ses_fault",
      messageID: m.id,
      type: "step-finish",
      reason: "stop",
      cost: 0,
      tokens: { input, output: 4, reasoning: 1, cache: { read: 3, write: 0 } },
    });
    await h.event({
      event: { type: "message.updated", properties: { info: m } },
    });
    for (const p of [
      step("prt_step1", 10),
      step("prt_step2", 20),
      step("prt_step1", 10),
    ])
      await h.event({
        event: { type: "message.part.updated", properties: { part: p } },
      });
    let r = (await f.stored()).runs.ses_fault;
    assert.equal(r.queue.filter((e: any) => e.kind === "USAGE").length, 2);
    assert.equal(
      r.queue.find((e: any) => e.kind === "USAGE").usage.basis,
      "OPENCODE_COMPLETED_STEP_PART",
    );
    assert.equal(
      r.queue.find((e: any) => e.kind === "USAGE").usage.provider_request_id,
      null,
    );
    f.state.messages.set(m.id, {
      info: m,
      parts: [step("prt_step1", 10), step("prt_step2", 20)],
    });
    await h.dispose();
    await sleep(50);
    await f.plugin();
    await eventually(async () =>
      (await f.stored()).runs.ses_fault.queue.some(
        (e: any) => e.kind === "USAGE_EXPORT_RECONCILED",
      ),
    );
    r = (await f.stored()).runs.ses_fault;
    assert.equal(r.queue.filter((e: any) => e.kind === "USAGE").length, 2);
  } finally {
    await f.close();
  }
});

test("C: factory rejects dirty start; proposal hook captures every observed source change", async () => {
  const f = await fixture();
  try {
    await writeFile(join(f.directory, "source.py"), "def value(): return 2\n");
    const h: any = await f.plugin();
    await assert.rejects(
      () => h["chat.message"]({ sessionID: "ses_dirty" }, f.output()),
      /DIRTY_START/,
    );
    await writeFile(join(f.directory, "source.py"), "def value(): return 1\n");
    await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
    await writeFile(join(f.directory, "source.py"), "def value(): return 2\n");
    await writeFile(join(f.directory, "extra.py"), "x=3\n");
    const input = {
      sessionID: "ses_fault",
      tool: "chronosgraph_propose_change_for_approval",
      callID: "prop",
    };
    await assert.rejects(
      () =>
        h["tool.execute.before"](input, {
          args: { proposed_files: { "source.py": "def value(): return 2\n" } },
        }),
      /MISMATCH/,
    );
    const output: any = {
      args: {
        proposed_files: {
          "source.py": "def value(): return 2\n",
          "extra.py": "x=3\n",
        },
      },
    };
    await h["tool.execute.before"](input, output);
    assert.equal(output.args.candidate_origin, "OBSERVED_WORKTREE");
    assert.equal(output.args.candidate_manifest.entries.length, 2);
    assert.match(output.args.candidate_digest, /^[a-f0-9]{64}$/);
    assert.equal(
      output.args.overlay_digest,
      (await f.stored()).runs.ses_fault.overlay_digest,
    );
  } finally {
    await f.close();
  }
});

test("B measurement: same-machine ordinary tool hook samples (fault fixture, not provider timing)", async () => {
  const samples: { mode: string; sample: number; elapsed_ms: number }[] = [];
  for (const mode of ["healthy", "outage"]) {
    const f = await fixture();
    try {
      f.state.eventStatus = mode === "healthy" ? 200 : 503;
      f.state.eventDelay = mode === "healthy" ? 0 : 1200;
      const h: any = await f.plugin();
      await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
      for (let i = 0; i < 20; i++) {
        const t = performance.now();
        await h["tool.execute.before"](
          { sessionID: "ses_fault", tool: "read", callID: `measure_${i}` },
          { args: {} },
        );
        const elapsed_ms = performance.now() - t;
        samples.push({ mode, sample: i + 1, elapsed_ms });
        assert.ok(
          elapsed_ms < 250,
          `predeclared 250ms local-persistence budget exceeded: ${elapsed_ms}`,
        );
      }
    } finally {
      await f.close();
    }
  }
  console.log(
    "HOOK_MEASUREMENT_JSON=" +
      JSON.stringify({
        basis:
          "actual factory + real local files + controlled HTTP fault fixture; not agent/model timing",
        budget_ms: 250,
        samples,
      }),
  );
});

test("F: late explicit parent survives an already-created local run", async () => {
  const f = await fixture();
  try {
    const h: any = await f.plugin();
    await h["chat.message"]({ sessionID: "ses_fault" }, f.output());
    await h.event({
      event: {
        type: "session.created",
        properties: { info: { id: "ses_fault", parentID: "ses_parent" } },
      },
    });
    await sleep(80);
    assert.equal(
      (await f.stored()).runs.ses_fault.parent_session_id,
      "ses_parent",
    );
    assert.ok(
      f.state.requests.some(
        (e: any) =>
          e.kind === "SESSION_LINKED" && e.parent_session_id === "ses_parent",
      ),
    );
  } finally {
    await f.close();
  }
});
