/** Share pure response helpers between the preview and regression tests. */
export function queryString(values: Record<string, string | number | boolean>): string {
  return new URLSearchParams(Object.entries(values).map(([k, v]) => [k, String(v)])).toString();
}
export function formatBytes(bytes: number): string {
  return bytes < 1024 ? `${bytes} B` : `${(bytes / 1024).toFixed(1)} KiB`;
}
export function finalStateInput(text: string): Record<string, string | null> {
  const value: unknown = JSON.parse(text);
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Expected a JSON object mapping file paths to final source or null.");
  const entries = Object.entries(value);
  if (!entries.length || entries.length > 20 || entries.some(([, v]) => v !== null && typeof v !== "string"))
    throw new Error("Provide 1–20 file paths; each value must be final source text or null (delete).");
  return Object.fromEntries(entries) as Record<string, string | null>;
}
