import { useEffect, useState } from "react";
import { explain } from "../lib/api";
import { PROVIDER_LABELS, type AiSettings, type AnalysisResult } from "../types";

interface Props {
  settings: AiSettings;
  content: string;
  result: AnalysisResult;
}

export default function AiExplanation({ settings, content, result }: Props) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { setText(""); setError(""); }, [result]);

  const run = async () => {
    setBusy(true);
    setError("");
    try {
      setText((await explain(settings, content, result)).explanation);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-2 rounded-2xl border border-stone-200 p-4 dark:border-stone-800">
      {!text && (
        <>
          <button onClick={run} disabled={busy} className="w-full rounded-xl border border-teal-700 py-3 font-semibold text-teal-800 disabled:opacity-60 dark:text-teal-300">
            {busy ? "Asking…" : `✨ Explain with AI (${PROVIDER_LABELS[settings.provider]})`}
          </button>
          <p className="text-xs text-stone-500 dark:text-stone-400">Sends this message and the findings above to {PROVIDER_LABELS[settings.provider]} using your key. The verdict stays the same. AI only explains it.</p>
        </>
      )}
      {text && (
        <>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-stone-600 dark:text-stone-400">AI explanation</h3>
          <p className="whitespace-pre-wrap text-sm">{text}</p>
          <p className="text-xs text-stone-500">AI can make mistakes. The verdict above comes from fixed rules.</p>
        </>
      )}
      {error && <p role="alert" className="text-sm text-red-600 dark:text-red-400">{error}</p>}
    </section>
  );
}
