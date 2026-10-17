export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}
export async function request<T>(
  path: string,
  signal: AbortSignal,
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      signal: AbortSignal.any([signal, AbortSignal.timeout(30000)]),
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new ApiError(
      `Cannot reach ChronosGraph at ${API_BASE}. Check that the configured backend is running, then retry.`,
      0,
    );
  }
  const payload = await response.json().catch(() => null);
  if (signal.aborted) throw signal.reason || new DOMException('Request aborted', 'AbortError');
  if (!response.ok) {
    const detail =
      typeof payload?.detail === "string"
        ? payload.detail
        : JSON.stringify(payload?.detail ?? "Unexpected backend response");
    throw new ApiError(`HTTP ${response.status}: ${detail}`, response.status);
  }
  return payload as T;
}
export function safeUrl(value: unknown): string | undefined {
  if (typeof value !== "string") return;
  try {
    const u = new URL(value);
    if (u.protocol === "https:" || u.protocol === "http:") return u.href;
  } catch {}
}
export function text(value: unknown): string {
  return value == null
    ? "Not provided"
    : typeof value === "object"
      ? JSON.stringify(value)
      : String(value);
}
export function ms(value: number): string {
  return Number.isFinite(value) ? `${value.toFixed(2)} ms` : "Not measured";
}
export function timestamp(value: unknown): string {
  if (typeof value !== "number" || value === 0) return "Open / not set";
  const date = new Date(value * 1000);
  return Number.isNaN(date.valueOf())
    ? "Not provided"
    : date.toISOString().replace("T", " ").replace(".000Z", " UTC");
}
