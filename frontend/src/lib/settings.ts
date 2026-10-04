import type { AiSettings, Provider } from "../types";

// The key lives ONLY in this browser's localStorage. It is sent to the backend solely
// inside an explicit "Explain with AI" request and is never saved server-side.
const KEY = "vidhur.ai.v1";
const PROVIDERS: Provider[] = ["openai", "anthropic", "gemini", "grok"];

export function loadSettings(): AiSettings | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    if (PROVIDERS.includes(s.provider) && typeof s.apiKey === "string" && s.apiKey.length >= 8) {
      return { provider: s.provider, apiKey: s.apiKey, model: typeof s.model === "string" ? s.model : "" };
    }
  } catch {
    /* storage unavailable or corrupt: behave as "no key set" */
  }
  return null;
}

export function saveSettings(s: AiSettings): boolean {
  try {
    localStorage.setItem(KEY, JSON.stringify(s));
    return true;
  } catch {
    return false;
  }
}

export function clearSettings() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
