import { useState } from "react";
import AiExplanation from "./components/AiExplanation";
import QrScanner from "./components/QrScanner";
import EmergencyHelp from "./components/EmergencyHelp";
import PlaybookCard from "./components/PlaybookCard";
import ScreenshotInput from "./components/ScreenshotInput";
import SettingsPanel from "./components/SettingsPanel";
import VerdictCard from "./components/VerdictCard";
import { analyze, ocr } from "./lib/api";
import { prepareImage } from "./lib/image";
import { loadSettings } from "./lib/settings";
import { useServerStatus } from "./lib/useServerStatus";
import type { AiSettings, AnalysisResult, Mode } from "./types";

const TABS: { mode: Mode; label: string; icon: string }[] = [
  { mode: "text", label: "Message", icon: "💬" },
  { mode: "url", label: "Link", icon: "🔗" },
  { mode: "qr", label: "QR", icon: "▦" },
  { mode: "screenshot", label: "Screenshot", icon: "📱" },
];

export default function App() {
  const { status, retry } = useServerStatus();
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [checked, setChecked] = useState(""); // the exact content that was analysed (shown + sent to AI on request)
  const [checkedLabel, setCheckedLabel] = useState("");
  const [fileName, setFileName] = useState("");
  const [settings, setSettings] = useState<AiSettings | null>(loadSettings);
  const [showSettings, setShowSettings] = useState(false);
  const [view, setView] = useState<"check" | "emergency">("check");

  const ready = status === "ready";
  const disabled = busy || !ready;

  const run = async (fn: () => Promise<{ content: string; result: AnalysisResult; label?: string }>) => {
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const r = await fn();
      setChecked(r.content);
      setCheckedLabel(r.label ?? "");
      setResult(r.result);
      setTimeout(() => document.getElementById("result")?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const checkText = () => run(async () => ({ content: text, result: await analyze(text, "text") }));
  const checkUrl = () => run(async () => ({ content: url.trim(), result: await analyze(url.trim(), "url") }));
  const checkQr = (decoded: string) =>
    run(async () => ({ content: decoded, label: "QR code contains", result: await analyze(decoded, "qr") }));
  const checkShot = (file: File) => {
    setFileName(file.name);
    return run(async () => {
      const blob = await prepareImage(file);
      const r = await ocr(blob);
      return { content: r.text, label: "Text read from your screenshot", result: r.result };
    });
  };

  const switchMode = (m: Mode) => {
    setMode(m);
    setResult(null);
    setError("");
  };

  if (view === "emergency") {
    return (
      <div className="mx-auto min-h-dvh max-w-xl px-4 pb-10 pt-[max(1rem,env(safe-area-inset-top))]">
        <EmergencyHelp initialLang={result?.language ?? "en"} initialMessage={checked} onBack={() => setView("check")} />
      </div>
    );
  }

  const canCheck = mode === "text" ? text.trim().length > 0 : url.trim().length > 0;

  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col px-4 pb-10 pt-[max(1rem,env(safe-area-inset-top))]">
      <header className="flex items-center justify-between py-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-extrabold tracking-tight">
            <img src="/favicon.svg" alt="" className="h-8 w-8" /> Vidhur
          </h1>
          <p className="text-sm text-stone-600 dark:text-stone-400">Check before you trust.</p>
        </div>
        <button onClick={() => setShowSettings(true)} aria-label="AI settings" className="relative rounded-full border border-stone-300 px-3 py-2 text-sm dark:border-stone-700">
          ⚙️ AI{settings && <span className="ml-1 text-teal-600">●</span>}
        </button>
      </header>

      {status !== "ready" && (
        <div role="status" className="mb-3 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
          {status === "offline" ? (
            <div className="flex items-center justify-between gap-3">
              <span>Couldn't reach the server. Check your internet.</span>
              <button onClick={retry} className="rounded-lg bg-amber-600 px-3 py-1 font-semibold text-white">Retry</button>
            </div>
          ) : status === "waking" ? (
            <span>⏳ Waking up the server… this can take up to a minute. It is free, so it sleeps when nobody is using it.</span>
          ) : (
            <span>Connecting to the server…</span>
          )}
        </div>
      )}

      <nav role="tablist" aria-label="What do you want to check?" className="grid grid-cols-4 gap-1 rounded-2xl bg-stone-200 p-1 dark:bg-stone-800">
        {TABS.map((t) => (
          <button
            key={t.mode}
            role="tab"
            aria-selected={mode === t.mode}
            onClick={() => switchMode(t.mode)}
            className={`flex flex-col items-center rounded-xl py-2 text-xs font-semibold ${mode === t.mode ? "bg-white shadow dark:bg-stone-950" : "text-stone-600 dark:text-stone-400"}`}
          >
            <span className="text-lg" aria-hidden>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>

      <main className="mt-4 space-y-4">
        {mode === "text" && (
          <div className="space-y-3">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={6}
              maxLength={10000}
              placeholder="Paste the message here (SMS, WhatsApp, email…). English, Hindi or Hinglish."
              className="w-full rounded-2xl border border-stone-300 bg-white p-3 text-base dark:border-stone-700 dark:bg-stone-900"
            />
            <CheckButton onClick={checkText} disabled={disabled || !canCheck} busy={busy} ready={ready} />
          </div>
        )}

        {mode === "url" && (
          <div className="space-y-3">
            <input
              type="url" inputMode="url" value={url} onChange={(e) => setUrl(e.target.value)}
              autoCapitalize="off" autoCorrect="off" spellCheck={false}
              placeholder="Paste the link, e.g. https://…"
              className="w-full rounded-2xl border border-stone-300 bg-white p-3 text-base dark:border-stone-700 dark:bg-stone-900"
            />
            <p className="text-xs text-stone-500 dark:text-stone-400">Vidhur never opens the link. It only studies the address, so it is safe to check scam links here.</p>
            <CheckButton onClick={checkUrl} disabled={disabled || !canCheck} busy={busy} ready={ready} />
          </div>
        )}

        {mode === "qr" && <QrScanner disabled={disabled} onDecoded={checkQr} />}
        {mode === "screenshot" && <ScreenshotInput disabled={disabled} onFile={checkShot} fileName={fileName} />}

        {busy && <p role="status" className="text-center text-sm text-stone-600 dark:text-stone-400">{mode === "screenshot" ? "Reading your screenshot…" : "Checking…"}</p>}
        {error && <p role="alert" className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-200">{error}</p>}

        {result && (
          <div id="result" className="scroll-mt-4 space-y-4">
            {checkedLabel && (
              <details className="rounded-xl border border-stone-200 p-3 text-sm dark:border-stone-800" open={mode === "qr"}>
                <summary className="cursor-pointer font-medium">{checkedLabel}</summary>
                <p className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-all text-stone-700 dark:text-stone-300">{checked}</p>
              </details>
            )}
            <VerdictCard result={result} />
            {result.playbook && <PlaybookCard playbook={result.playbook} lang={result.language ?? "en"} />}
            {settings && <AiExplanation settings={settings} content={checked} result={result} />}
          </div>
        )}

        <button
          onClick={() => setView("emergency")}
          className="w-full rounded-2xl border-2 border-stone-300 px-4 py-4 text-center text-base font-semibold text-stone-800 active:bg-stone-100 dark:border-stone-700 dark:text-stone-200 dark:active:bg-stone-800"
        >
          🆘 Already paid or shared your OTP? Get help now
        </button>
      </main>

      <footer className="mt-auto pt-10 text-center text-xs text-stone-500 dark:text-stone-500">
        Free. No sign-up. Nothing you check is saved. Vidhur gives warning signs, not a guarantee, so when in doubt, contact the organisation directly.
      </footer>

      {showSettings && <SettingsPanel current={settings} onChange={setSettings} onClose={() => setShowSettings(false)} />}
    </div>
  );
}

function CheckButton({ onClick, disabled, busy, ready }: { onClick: () => void; disabled: boolean; busy: boolean; ready: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled} className="w-full rounded-2xl bg-teal-700 py-4 text-lg font-bold text-white disabled:opacity-50 active:bg-teal-800">
      {!ready ? "Waiting for server…" : busy ? "Checking…" : "Check"}
    </button>
  );
}
