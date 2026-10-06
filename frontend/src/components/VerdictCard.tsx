import type { AnalysisResult, Lang, Severity, Verdict } from "../types";

const CONSEQUENCE_HEADING: Record<Lang, string> = {
  en: "What could happen if you go ahead",
  hi: "आगे बढ़ने पर क्या हो सकता है",
  hinglish: "Aage badhne par kya ho sakta hai",
};

const VERDICT: Record<Verdict, { label: string; icon: string; sub: string; box: string; badge: string }> = {
  safe: {
    label: "Safe", icon: "✅", sub: "No known scam signs found.",
    box: "border-emerald-300 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950/40",
    badge: "bg-emerald-600 text-white",
  },
  suspicious: {
    label: "Suspicious", icon: "⚠️", sub: "Some warning signs. Check before you trust it.",
    box: "border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/40",
    badge: "bg-amber-500 text-black",
  },
  high_risk: {
    label: "High Risk", icon: "🚫", sub: "This looks like a scam. Do not engage.",
    box: "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/40",
    badge: "bg-red-600 text-white",
  },
};

const SEV: Record<Severity, { label: string; cls: string }> = {
  high: { label: "Serious", cls: "bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-200" },
  medium: { label: "Warning", cls: "bg-amber-100 text-amber-900 dark:bg-amber-900/60 dark:text-amber-100" },
  low: { label: "Note", cls: "bg-stone-200 text-stone-800 dark:bg-stone-700 dark:text-stone-100" },
};

export default function VerdictCard({ result }: { result: AnalysisResult }) {
  const v = VERDICT[result.verdict];
  return (
    <section aria-live="polite" className={`space-y-4 rounded-2xl border p-4 ${v.box}`}>
      <div className="flex items-center gap-3">
        <span className="text-3xl" aria-hidden>{v.icon}</span>
        <div>
          <span className={`inline-block rounded-full px-3 py-1 text-lg font-bold ${v.badge}`}>{v.label}</span>
          <p className="mt-1 text-sm text-stone-700 dark:text-stone-300">{v.sub}</p>
        </div>
      </div>

      {result.findings.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-600 dark:text-stone-400">
            {result.verdict === "safe" ? "Things to note" : "Why"}
          </h3>
          <ul className="space-y-2">
            {result.findings.map((f, i) => (
              <li key={f.id + i} className="rounded-xl bg-white/80 p-3 text-sm dark:bg-stone-900/70">
                <span className={`mr-2 inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${SEV[f.severity].cls}`}>{SEV[f.severity].label}</span>
                {f.reason}
                {f.evidence && <code className="mt-1 block break-all rounded bg-stone-100 px-2 py-1 text-xs text-stone-700 dark:bg-stone-800 dark:text-stone-300">{f.evidence}</code>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.consequences && result.consequences.length > 0 && (
        <div className="rounded-xl border-l-4 border-stone-400 bg-white/80 p-3 dark:border-stone-500 dark:bg-stone-900/70">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-600 dark:text-stone-400">
            {CONSEQUENCE_HEADING[result.language ?? "en"]}
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {result.consequences.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-xl bg-white p-3 dark:bg-stone-900">
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-stone-600 dark:text-stone-400">What to do</h3>
        <p className="font-medium">{result.next_step}</p>
        {result.report_hint && <p className="mt-2 text-sm text-stone-700 dark:text-stone-300">{result.report_hint}</p>}
      </div>
    </section>
  );
}
