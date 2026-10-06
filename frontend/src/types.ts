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

export type Lang = "en" | "hi" | "hinglish";

export interface Playbook {
  id: string;
  name: string;
  how_it_works: string[];
  what_next: string[];
  real_looks_like: string[];
}

export interface AnalysisResult {
  verdict: Verdict;
  findings: Finding[];
  next_step: string;
  report_hint?: string | null;
  language?: Lang;
  consequences?: string[];
  playbook?: Playbook | null;
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
