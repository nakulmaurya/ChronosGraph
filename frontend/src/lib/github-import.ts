/** Local-CLI setup only: these helpers never fetch or send a GitHub repository. */
export function githubIntakeCommands(url: string, branch: string, tenant: string, revision: string) {
  branch = branch.trim() || "main";
  tenant = tenant.trim();
  revision = revision.trim().toLowerCase();
  const match = /^https:\/\/github\.com\/([A-Za-z0-9][A-Za-z0-9_.-]{0,99})\/([A-Za-z0-9][A-Za-z0-9_.-]{0,99})\/?$/.exec(url);
  if (!match || [".", ".."].includes(match[2])) throw new Error("Use https://github.com/owner/repo without credentials, query or tree paths.");
  if (!/^[A-Za-z0-9_./-]{1,200}$/.test(branch) || /^[-./]/.test(branch) || /[./]$/.test(branch) || branch.includes("..") || branch.includes("//") || branch.split("/").some(p => p.startsWith(".") || p.endsWith(".lock")))
    throw new Error("Enter an explicit supported branch name.");
  const canonical = `https://github.com/${match[1]}/${match[2].replace(/\.git$/, "")}`;
  const base = `PYTHONPATH="$PWD/backend" .venv/bin/python -m app.ingestion.github_import`;
  const args = `--url '${canonical}' --branch '${branch}'`;
  const inspect = `${base} inspect ${args}`;
  const validImport = (!tenant || /^repo_[a-z0-9_]+$/.test(tenant)) && (!revision || /^[0-9a-f]{40}$/.test(revision));
  const savedName = tenant ? `'${tenant}'` : `"repo_github_$(.venv/bin/python -c 'import uuid; print(uuid.uuid4().hex)')"`;
  const resolveLatest = `revision="$(${inspect} | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["source_revision"])')"`;
  const command = `CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT=1 ${base} import ${args} --tenant ${savedName} --expected-head ${revision ? `'${revision}'` : '"$revision"'}`;
  const importCommand = validImport ? (revision ? command : `${resolveLatest} &&\n${command}`) : null;
  return { inspect, importCommand, usesLatest: !revision };
}
