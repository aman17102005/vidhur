import { useEffect, useRef, useState } from "react";
import { PROVIDER_LABELS, type AiSettings, type Provider } from "../types";
import { clearSettings, saveSettings } from "../lib/settings";

interface Props {
  current: AiSettings | null;
  onChange: (s: AiSettings | null) => void;
  onClose: () => void;
}

export default function SettingsPanel({ current, onChange, onClose }: Props) {
  const [provider, setProvider] = useState<Provider>(current?.provider ?? "openai");
  const [apiKey, setApiKey] = useState(current?.apiKey ?? "");
  const [model, setModel] = useState(current?.model ?? "");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  const save = () => {
    const key = apiKey.trim();
    if (key.length < 8) return setError("Paste your full API key.");
    const s = { provider, apiKey: key, model: model.trim() };
    if (!saveSettings(s)) return setError("Your browser blocked saving. The key will work only until you close this page.");
    onChange(s);
    onClose();
  };

  const remove = () => {
    clearSettings();
    onChange(null);
    onClose();
  };

  const input = "w-full rounded-xl border border-stone-300 bg-white px-3 py-3 text-base dark:border-stone-700 dark:bg-stone-900";

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      className="m-auto w-[min(92vw,28rem)] rounded-2xl bg-white p-0 text-stone-900 shadow-xl backdrop:bg-black/50 dark:bg-stone-900 dark:text-stone-100"
    >
      <div className="space-y-4 p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">AI explanation (optional)</h2>
          <button onClick={onClose} aria-label="Close" className="-m-2 p-2 text-2xl leading-none text-stone-500">×</button>
        </div>
        <p className="text-sm text-stone-600 dark:text-stone-400">
          Vidhur works fully without this. If you add your own key, you can tap "Explain with AI" after a check to get a plain-language explanation.
        </p>

        <label className="block space-y-1">
          <span className="text-sm font-medium">AI provider</span>
          <select value={provider} onChange={(e) => setProvider(e.target.value as Provider)} className={input}>
            {(Object.keys(PROVIDER_LABELS) as Provider[]).map((p) => (
              <option key={p} value={p}>{PROVIDER_LABELS[p]}</option>
            ))}
          </select>
        </label>

        <label className="block space-y-1">
          <span className="text-sm font-medium">Your API key</span>
          <div className="flex gap-2">
            <input
              type={show ? "text" : "password"}
              value={apiKey}
              onChange={(e) => { setApiKey(e.target.value); setError(""); }}
              autoComplete="off" autoCorrect="off" autoCapitalize="off" spellCheck={false}
              placeholder="Paste key here"
              className={input}
            />
            <button type="button" onClick={() => setShow((v) => !v)} className="shrink-0 rounded-xl border border-stone-300 px-3 text-sm dark:border-stone-700">
              {show ? "Hide" : "Show"}
            </button>
          </div>
        </label>

        <details className="text-sm">
          <summary className="cursor-pointer text-stone-600 dark:text-stone-400">Advanced: choose a model</summary>
          <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="Leave empty for the default" className={`${input} mt-2`} spellCheck={false} />
        </details>

        <p className="rounded-xl bg-stone-100 p-3 text-xs text-stone-600 dark:bg-stone-800 dark:text-stone-400">
          🔒 Your key is saved only in this browser. Vidhur's server never stores it: it is used for the single request you trigger, then discarded. Your message is sent to {PROVIDER_LABELS[provider]} only when you tap "Explain with AI". Don't use this on a shared device.
        </p>

        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}

        <div className="flex gap-2">
          <button onClick={save} className="flex-1 rounded-xl bg-teal-700 py-3 font-semibold text-white active:bg-teal-800">Save</button>
          {current && <button onClick={remove} className="rounded-xl border border-red-300 px-4 py-3 font-medium text-red-700 dark:border-red-800 dark:text-red-400">Remove key</button>}
        </div>
      </div>
    </dialog>
  );
}
