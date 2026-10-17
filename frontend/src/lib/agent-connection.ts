/** Build data-only stdio configuration. No shell command or installation is run. */
export type AgentSetup = {
  backendDirectory: string;
  pythonExecutable: string;
  databaseHost: string;
  databasePort: string;
};
export function buildAgentConfig(setup: AgentSetup): string {
  const cwd = setup.backendDirectory.trim();
  const python = setup.pythonExecutable.trim();
  const host = setup.databaseHost.trim();
  if (!cwd.startsWith("/") || /[\r\n\0]/.test(cwd))
    throw new Error("Enter an absolute backend directory on the machine running the agent.");
  if (!python || /[\r\n\0]/.test(python) || (!python.startsWith("/") && /[\s/]/.test(python)))
    throw new Error("Enter a Python executable name or absolute path, not a shell command.");
  if (!host || /[\s\0]/.test(host))
    throw new Error("Enter the FalkorDB host reachable from the agent machine.");
  if (!/^\d+$/.test(setup.databasePort) || Number(setup.databasePort) < 1 || Number(setup.databasePort) > 65535)
    throw new Error("Enter a database port from 1 to 65535.");
  return JSON.stringify({ mcpServers: { chronosgraph: {
    command: python, args: ["-m", "app.mcp_server.server"], cwd,
    env: { FALKORDB_HOST: host, FALKORDB_PORT: String(Number(setup.databasePort)) },
  } } }, null, 2);
}
export function buildSnapshotHandoff(tenant: string, revision: string | null): string | null {
  if (!/^repo_[a-z0-9_]+$/.test(tenant) || !revision || !/^[0-9a-f]{40}$/.test(revision)) return null;
  return [
    "Use the ChronosGraph MCP connection. Call discover_repositories and confirm this saved version is listed.",
    `Call inspect_repository_snapshot with ${JSON.stringify({ tenant_graph: tenant, expected_revision: revision })}.`,
    `Pass ${JSON.stringify({ tenant_graph: tenant, expected_revision: revision })} on every subsequent tool call; never fall back to a default tenant.`,
    "If discovery or the guard disagrees, stop and ask which version to use. This is a saved snapshot, not a live workspace.",
    "Locate context, read exact symbol source, preview the proposed diff, and report candidate tests and unresolved coverage before requesting human approval.",
    "Do not apply code or override policy without approval. Saved findings are agent-reported evidence, not independently executed tests.",
  ].join("\n\n");
}
