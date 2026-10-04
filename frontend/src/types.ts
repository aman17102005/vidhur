export type Severity = "low" | "medium" | "high";
export type Verdict = "safe" | "suspicious" | "high_risk";
export type Mode = "text" | "url" | "qr" | "screenshot";

export interface Finding {
  id: string;
  severity: Severity;
  reason: string;
  evidence?: string | null;
  action: string;
}

export interface AnalysisResult {
  verdict: Verdict;
  findings: Finding[];
  next_step: string;
  report_hint?: string | null;
}

export type Provider = "openai" | "anthropic" | "gemini" | "grok";

export interface AiSettings {
  provider: Provider;
  apiKey: string;
  model: string;
}

export const PROVIDER_LABELS: Record<Provider, string> = {
  openai: "OpenAI",
  anthropic: "Claude (Anthropic)",
  gemini: "Gemini (Google)",
  grok: "Grok (xAI)",
};
