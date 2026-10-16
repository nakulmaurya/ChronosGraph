# T-09 platform and runtime boundaries

## Runtime

Frontend runtime minimum is **Node 20.9** (Next.js requirement); Node 22 and 24
are also targeted. Tests use a test-only TypeScript loader backed by the locked
`typescript` development dependency, not Node 24's native type stripping.
`npm run typecheck` remains mandatory: transpilation alone is not type checking.
Do not use `npm ci --omit=dev` before running tests or building.

The Bash launcher refuses Node 20.0–20.8 and older releases. This is not a
promise that every future odd-numbered Node release is tested.

## Linux

The live integration environment is Debian 13 with Docker FalkorDB 4.22.1,
Python virtual environment, Node and Chromium. Use the README launcher for an
ephemeral local demo. `--db existing` reuses only a trusted local FalkorDB.
Use an explicitly configured persistent database for long-lived findings;
launcher-owned `--rm` containers intentionally do not preserve memory.

## macOS

Use Docker Desktop and a compatible Python 3.11+ virtual environment, Node
20.9+/22/24, Git and Bash. Follow README commands from Terminal. Native
`falkordblite` is an optional platform-dependent path, not a tested macOS release
gate. **macOS execution NOT RUN in this checkpoint.**

## Windows

Use **WSL2** with Git/Bash/Python/Node inside the same Linux environment and
Docker Desktop WSL integration. Run the README launcher from that WSL shell.
Do not mix Windows and WSL virtual-environment or `node_modules` directories.
Native Win32 `falkordblite` is unsupported; choose Docker Desktop or WSL2.
The Bash launcher is not a PowerShell script. **Windows/WSL execution NOT RUN.**

For an MCP client running outside WSL, configure its supported WSL stdio launcher
and absolute backend path; confirm with that client's documentation. The generic
MCP template is not an automatically installed IDE integration.

## Safety

Keep API/UI/database loopback-only. Remote VM access uses SSH port forwarding;
opening a browser does not require exposing the ports to the Internet.
No paid model credential is required for ingestion, graph analysis or MCP tools.
Untrusted repository code and suggested verification commands are never executed
by the diff or finding services.