import type { AiSettings, AnalysisResult, Finding, Mode } from "../types";

export const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {}

async function request<T>(path: string, init: RequestInit, timeoutMs = 70_000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(API_URL + path, { ...init, signal: ctrl.signal, cache: "no-store" });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new ApiError(typeof body.detail === "string" ? body.detail : "Something went wrong. Please try again.");
    return body as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if ((e as Error).name === "AbortError") throw new ApiError("The server took too long to answer. Please try again.");
    throw new ApiError("Could not reach the server. Check your internet and try again.");
  } finally {
    clearTimeout(timer);
  }
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const health = () => request<{ status: string }>("/health", { method: "GET" }, 8_000);

export const analyze = (content: string, mode: Mode) => request<AnalysisResult>("/analyze", json({ content, mode }));

// Screenshot goes as the raw request body so the server never spools it to disk.
export const ocr = (image: Blob) =>
  request<{ text: string; result: AnalysisResult }>("/ocr", { method: "POST", headers: { "Content-Type": image.type || "image/jpeg" }, body: image });

export const explain = (s: AiSettings, content: string, result: AnalysisResult) =>
  request<{ explanation: string }>(
    "/explain",
    json({
      provider: s.provider,
      api_key: s.apiKey,
      model: s.model || null,
      content,
      verdict: result.verdict,
      findings: result.findings as Finding[],
    }),
  );
