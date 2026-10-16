// Test-only transpilation, shared by Node 20.9+, 22 and 24.
// Type correctness remains a separate `npm run typecheck` gate.
import { register } from "node:module";
register("./typescript-loader.mjs", import.meta.url);