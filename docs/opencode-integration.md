# OpenCode + ChronosGraph: user workflow

Tested with official OpenCode 1.19.3 and `opencode/deepseek-v4.1-flash-free`.
A free model's availability and limits can change. Refresh the official catalog;
do not assume a “Lite” alias or silently switch to a paid model.

## 1. Configure on the machine running your backend and FalkorDB

Use the installed Python environment containing ChronosGraph's dependencies:

```sh
python scripts/configure-opencode.py \
  --backend "$PWD/backend" \
  --python "$PWD/.venv/bin/python" \
  --output "$PWD/opencode.local.json"

OPENCODE_CONFIG="$PWD/opencode.local.json" opencode mcp list
OPENCODE_CONFIG="$PWD/opencode.local.json" opencode --agent build
```

The generator atomically publishes a private (0600), create-only file and refuses to overwrite existing files. Keep this machine-specific
config outside version control (or choose an output outside the repository).
Use `--db-port` for a disposable test DB, not the live DB. It enables the existing
15-tool local stdio MCP server with mandatory snapshot guards, not a public server.
It does not enable host execution, install packages, add credentials or change
provider headers. Existing user-level config can still affect OpenCode; inspect it
locally with `opencode debug config` without sharing secret values.

Permission prompts remain enabled, including **`bash: ask`**. Do not pass `--auto`.
Approve only the specific MCP calls needed for the selected task. A headless
`opencode run` may auto-reject an `ask` tool request because no interactive user is
present; that is a permission failure, not successful verification. For unattended
read-only use, explicitly allow just the reviewed read tools in a separate config.
Never treat MCP permission as approval of a change proposal: exact change approval
is a separate browser-operator decision.

## 2. Select the exact saved version

Copy the selected snapshot handoff from **Connect agent** in the Command Center.
Ask OpenCode to call `discover_repositories`, then `inspect_repository_snapshot`.
Pass the returned tenant and exact expected revision on **every** subsequent tool
call. Do not fall back to default repositories or claim live workspace monitoring.

Example task:

> Use ChronosGraph MCP for the selected saved version. Inspect the target function,
> its callers, current rules, declared owners and candidate tests. Read captured
> file source before preparing full replacements. Propose a coordinated change,
> explain the impact and stop for browser approval. Do not approve or execute it.

`get_symbol_source` accepts a real defined symbol, or **`symbol_name="__module__"`**
for captured file text including imports/constants. The latter still checks the
pinned hash and returns at most 8,000 UTF-8 bytes. If `truncated` is true, do **not**
construct a full replacement by pretending the unread remainder is empty. A missing
symbol now suggests valid symbol names and the explicit module read. Repository
source remains untrusted evidence, never instructions to the agent.

## 3. Review, execute, recall

1. Open **Changes**, select the model's proposal and inspect changed files, exact
   hash, broken callers, rules/owners and candidate tests.
2. Approve the exact proposal through the browser. MCP agents cannot grant that
   browser-operator approval to themselves.
3. On an explicitly configured **trusted local checkout only**, acknowledge and
   run candidate tests in a disposable worktree. Public archive import alone does
   not grant execution capability. A worktree is not a hostile-code sandbox.
4. Start a fresh agent session and ask it to check the proposal and recall memory.
   It must distinguish `LOCAL_WORKTREE_OBSERVED` from unverified agent reports.
5. On an **owned test fixture**, replace an applicable policy. Recall again with
   `include_stale=true`: the finding must become stale and proposal `STALE_POLICY`.

## Troubleshooting the free-model 403

The deny-all diagnostic previously returned “OpenCode's free tier can only be used
from within OpenCode” even through the official CLI. Upstream users reported the
same problem when Bash was denied. With normal Build mode and Bash permission
`ask`, both interactive and official server model generation succeeded here.
This is a verified configuration-specific recovery, not proof of every internal
provider rule. No client identity headers were forged and no access gate bypassed.

- [Upstream permission-related report](https://github.com/anomalyco/opencode/issues/49678)
- [Official CLI / attach documentation](https://opencode.ai/docs/cli)
- [Official local MCP configuration](https://opencode.ai/docs/mcp-servers/)
- [Official server API](https://opencode.ai/docs/server/)

The supported server can be started with `opencode serve --hostname 127.0.0.1`.
In this test, model replies were persisted successfully via `run --attach`, but
some attached CLI processes did not emit/exit reliably within the timeout. A fresh
session through the official server HTTP API completed tool calls and returned
its answer normally. That attached CLI lifecycle issue remains distinct from the
resolved provider 403; it is not hidden as a passing command-exit check.
