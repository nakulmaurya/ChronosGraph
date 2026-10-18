/** Linux single-writer, durable local queue. Network work never holds local hook serialization. */
import { createHash, randomUUID } from "node:crypto";
import { spawn, type ChildProcess } from "node:child_process";
import {
  mkdir,
  readFile,
  writeFile,
  open,
  rename,
  chmod,
} from "node:fs/promises";
import { join } from "node:path";
export const fingerprint = (x: unknown) =>
  createHash("sha256").update(JSON.stringify(x)).digest("hex");
export type Binding = {
  api_url: string;
  tenant_graph: string;
  expected_revision: string;
  task_id: string;
  plan_id: string;
  pack_id: string;
};
export type Envelope = Record<string, unknown> & {
  sequence: number;
  source_event_id: string;
  event_id: string;
  observed_at_ms: number;
};
export type Delivery = {
  id: string;
  message_id: string;
  part_id: string;
  status: "PREPARED" | "INJECTED_UNCONFIRMED" | "HOST_PART_OBSERVED";
  block_digest: string;
  injection_bytes: number;
  estimated_token_equivalents: number;
};
export type Transport = {
  attempts: number;
  retry_at: number;
  last_error: string | null;
  blocked: { envelope: Envelope; reason: string; at: number }[];
  reconciliation_required: boolean;
  saturated: boolean;
  unobserved_count: number;
};
export type Run = {
  id: string;
  overlay_digest: string;
  session_id: string;
  sequence: number;
  seen: Record<string, string>;
  queue: Envelope[];
  delivery?: Delivery;
  transport: Transport;
  parent_session_id?: string;
};
type State = { version: 2; binding: Binding; runs: Record<string, Run> };
export class BridgeHttpError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(`Bridge HTTP ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}
const defaults = (): Transport => ({
  attempts: 0,
  retry_at: 0,
  last_error: null,
  blocked: [],
  reconciliation_required: false,
  saturated: false,
  unobserved_count: 0,
});
const pause = (ms: number) => new Promise((r) => setTimeout(r, ms));
export class LocalRuntime {
  state: State;
  private file: string;
  private writer: ChildProcess;
  private local = Promise.resolve();
  private timer: ReturnType<typeof setTimeout> | undefined;
  private active: Promise<void> | undefined;
  private abort: AbortController | undefined;
  private closed = false;
  private binding: Binding;
  private log: (message: string) => void;
  private constructor(
    directory: string,
    binding: Binding,
    log: (message: string) => void,
    writer: ChildProcess,
    state: State,
  ) {
    this.binding = binding;
    this.log = log;
    this.file = join(directory, "telemetry-state.json");
    this.writer = writer;
    this.state = state;
    writer.once("exit", () => {
      if (!this.closed) {
        this.closed = true;
        this.abort?.abort();
        this.log(
          "Writer lock process exited; further mutations refused. Restart/reconcile project state.",
        );
      }
    });
  }
  static async open(
    directory: string,
    binding: Binding,
    log: (message: string) => void,
  ) {
    await mkdir(directory, { recursive: true, mode: 0o700 });
    // Kernel flock releases on process death/EOF; no unsafe stale-PID lock stealing.
    const writer = spawn(
      "flock",
      [
        "--nonblock",
        join(directory, "writer.lock"),
        "sh",
        "-c",
        'printf "LOCKED\\n"; cat >/dev/null',
      ],
      { stdio: ["pipe", "pipe", "pipe"] },
    );
    try {
      await new Promise<void>((resolve, reject) => {
        const timer = setTimeout(
          () => reject(Error("Writer lock handshake timeout")),
          1500,
        );
        const stop = (error?: Error) => {
          clearTimeout(timer);
          error ? reject(error) : resolve();
        };
        writer.once("error", (e) => stop(e));
        writer.once("exit", () =>
          stop(Error("Another writer owns this project state lock")),
        );
        writer.stdout!.once("data", (d) =>
          String(d).startsWith("LOCKED")
            ? stop()
            : stop(Error("Invalid writer lock handshake")),
        );
      });
      await chmod(join(directory, "writer.lock"), 0o600);
      let state: State = { version: 2, binding, runs: {} };
      try {
        const raw = await readFile(
          join(directory, "telemetry-state.json"),
          "utf8",
        );
        const old = JSON.parse(raw);
        if (fingerprint(old.binding) !== fingerprint(binding))
          throw Error(
            "Binding changed; archive old state and explicitly rebind",
          );
        if (![1, 2].includes(old.version))
          throw Error("Unsupported local state version");
        if (old.version === 1) {
          try {
            await writeFile(
              join(directory, "telemetry-state.v1-backup.json"),
              raw,
              { flag: "wx", mode: 0o600 },
            );
          } catch (e) {
            if ((e as NodeJS.ErrnoException).code !== "EEXIST") throw e;
          }
        }
        state = { ...old, version: 2 };
        for (const r of Object.values(state.runs)) {
          r.transport ??= defaults();
          r.queue ??= [];
          r.seen ??= {};
        }
      } catch (e) {
        if ((e as NodeJS.ErrnoException).code !== "ENOENT") throw e;
      }
      const rt = new LocalRuntime(directory, binding, log, writer, state);
      await rt.save();
      rt.schedule();
      return rt;
    } catch (e) {
      writer.stdin?.end();
      writer.kill();
      throw e;
    }
  }
  async save() {
    const tmp = `${this.file}.${randomUUID()}.tmp`;
    const f = await open(tmp, "wx", 0o600);
    try {
      await f.writeFile(JSON.stringify(this.state));
      await f.sync();
    } finally {
      await f.close();
    }
    await rename(tmp, this.file);
    const dir = await open(join(this.file, ".."), "r");
    try {
      await dir.sync();
    } finally {
      await dir.close();
    }
  }
  serial<T>(action: () => Promise<T>): Promise<T> {
    if (this.closed) return Promise.reject(Error("Project writer is disposed"));
    const result = this.local.then(action);
    this.local = result.then(
      () => {},
      (e) =>
        this.log(
          `Local persistence/hook failed: ${e instanceof Error ? e.message : "unknown"}`,
        ),
    );
    return result;
  }
  async request(path: string, body?: unknown, telemetry = false) {
    const controller = new AbortController();
    if (telemetry) this.abort = controller;
    const timeout = setTimeout(
      () => controller.abort(),
      telemetry ? 1500 : 8000,
    );
    try {
      const response = await fetch(
        `${this.binding.api_url.replace(/\/$/, "")}/api/v1/tasks/${path}`,
        {
          method: body === undefined ? "GET" : "POST",
          signal: controller.signal,
          headers: {
            "Content-Type": "application/json",
            "X-ChronosGraph-Action": "task-runtime",
          },
          ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        },
      );
      if (!response.ok) {
        let detail = "request rejected";
        try {
          detail = JSON.stringify(
            (await response.json()).detail ?? "request rejected",
          ).slice(0, 240);
        } catch {}
        throw new BridgeHttpError(response.status, detail);
      }
      return await response.json();
    } finally {
      clearTimeout(timeout);
      if (telemetry && this.abort === controller) this.abort = undefined;
    }
  }
  async enqueue(
    run: Run,
    kind: string,
    source: string,
    metadata: Record<string, unknown> = {},
  ) {
    const payload_digest = fingerprint({ kind, metadata }),
      key = `${source}:${payload_digest}`;
    if (run.seen[key]) {
      this.schedule();
      return;
    }
    if (
      run.queue.length + run.transport.blocked.length >= 250 ||
      Object.keys(run.seen).length >= 2000
    ) {
      run.transport.saturated = true;
      run.transport.unobserved_count++;
      run.transport.last_error =
        "Retention exhausted; event not recorded. Preserve immutable evidence and reconcile/start a new bounded run.";
      await this.save();
      this.log(run.transport.last_error);
      return;
    }
    const e: Envelope = {
      tenant_graph: this.binding.tenant_graph,
      expected_revision: this.binding.expected_revision,
      schema_version: 1,
      event_id: randomUUID(),
      source_event_id: key,
      sequence: ++run.sequence,
      kind,
      observed_at_ms: Date.now(),
      session_id: run.session_id,
      payload_digest,
      ...metadata,
    };
    run.seen[key] = e.event_id;
    run.queue.push(e);
    await this.save();
    this.schedule();
  }
  status(run: Run) {
    return {
      pending_count: run.queue.length,
      oldest_pending_age_ms: run.queue.length
        ? Math.max(0, Date.now() - run.queue[0].observed_at_ms)
        : 0,
      last_error: run.transport.last_error,
      blocked_count: run.transport.blocked.length,
      queue_saturated: run.transport.saturated,
      unobserved_count: run.transport.unobserved_count,
      reconciliation_required: run.transport.reconciliation_required,
      completeness: "NOT_PROVEN",
    };
  }
  private schedule(delay = 0) {
    if (this.closed || this.timer || this.active) return;
    this.timer = setTimeout(() => {
      this.timer = undefined;
      this.active = this.drain()
        .catch((e) => this.log(`Background telemetry: ${String(e)}`))
        .finally(() => {
          this.active = undefined;
          const pending = Object.values(this.state.runs).filter(
            (r) => r.queue.length && !r.transport.reconciliation_required,
          );
          if (pending.length)
            this.schedule(
              Math.max(
                10,
                Math.min(
                  ...pending.map((r) => r.transport.retry_at - Date.now()),
                ),
              ),
            );
        });
    }, delay);
    this.timer.unref();
  }
  private async drain() {
    for (let batch = 0; batch < 20 && !this.closed; batch++) {
      const next = await this.serial(async () => {
        for (const run of Object.values(this.state.runs))
          if (
            run.queue.length &&
            !run.transport.reconciliation_required &&
            run.transport.retry_at <= Date.now()
          )
            return { run, e: run.queue[0] };
      });
      if (!next) return;
      const { run, e } = next;
      let error: unknown;
      try {
        await this.request(
          `${this.binding.task_id}/runs/${run.id}/events`,
          e,
          true,
        );
      } catch (x) {
        error = x;
      }
      if (this.closed) return;
      await this.serial(async () => {
        if (run.queue[0]?.event_id !== e.event_id)
          throw Error("Queue head changed unexpectedly");
        if (!error) {
          run.queue.shift();
          run.transport.attempts = 0;
          run.transport.retry_at = 0;
          run.transport.last_error = null;
        } else {
          const status = error instanceof BridgeHttpError ? error.status : 0;
          run.transport.last_error =
            error instanceof Error ? error.message : "Network unavailable";
          if (
            [403, 404, 410].includes(status) ||
            (status === 409 &&
              /stale|revision|snapshot|binding/i.test(run.transport.last_error))
          ) {
            run.transport.reconciliation_required = true;
            this.log("RECONCILIATION_REQUIRED: " + run.transport.last_error);
          } else if (
            status >= 400 &&
            status < 500 &&
            ![408, 425, 429].includes(status)
          ) {
            run.queue.shift();
            run.transport.blocked.push({
              envelope: e,
              reason: run.transport.last_error,
              at: Date.now(),
            });
            this.log(
              "QUARANTINED: original event retained; " +
                run.transport.last_error,
            );
          } else {
            run.transport.attempts++;
            const delay = Math.min(
              15000,
              250 * 2 ** Math.min(run.transport.attempts - 1, 6),
            );
            run.transport.retry_at =
              Date.now() + Math.round(delay * (0.8 + Math.random() * 0.4));
          }
        }
        await this.save();
      });
    }
  }
  async dispose() {
    if (this.closed) return;
    clearTimeout(this.timer);
    const active = this.active;
    await Promise.race([active ?? Promise.resolve(), pause(400)]);
    this.closed = true;
    this.abort?.abort();
    await Promise.race([this.local, pause(100)]);
    void this.local.finally(() => this.writer.stdin?.end());
  }
}
