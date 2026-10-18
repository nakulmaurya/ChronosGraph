# Third-party source included in ChronosGraph

## modelcontextprotocol/python-sdk — retained comparison source context

Task 9 evidence includes pinned SDK source/diff context. See
[attribution and scope](third_party/README.md) and the verbatim
[upstream MIT copyright/permission notice](third_party/modelcontextprotocol-python-sdk-LICENSE).
Trial candidates are evidence, not upstream-approved or integrated SDK changes.

## sbdchd/codeowners — MIT

- Upstream: https://github.com/sbdchd/codeowners
- Pinned revision: `ad29fa77ce9726d97103cc49fbfcf4e295679034`
- Copied file: `codeowners/__init__.py` → `backend/app/_vendor/codeowners/__init__.py`
- License: `backend/app/_vendor/codeowners/LICENSE` (Steve Dignam copyright).
- Changes: none to the copied source. GitHub-subset validation and graph integration
  are separate original modules, not changes to this vendored file.
- The source also retains the MIT notice for Harry Marr's `path_to_regex` logic.
- Purpose: deterministic CODEOWNERS pattern matching without changing the shared
  VM Python environment or installing a full agent framework.

No source from Aider, Repomix, pathspec, Tree-sitter or context-mode is included by
this notice. They remain references/proposed integrations, not adopted dependencies.
