import { useMemo, useState } from "react";
import { buildComplaint } from "../lib/complaint";
import type { Lang } from "../types";
import emergency from "../data/emergency.json";

interface Props {
  lang: Lang;
  caseSummary: string;
  initialMessage: string;
}

// Runs fully in the browser. Nothing typed here is sent, stored or logged.
export default function ComplaintHelper({ lang, caseSummary, initialMessage }: Props) {
  const ui = emergency.ui;
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [amount, setAmount] = useState("");
  const [message, setMessage] = useState(initialMessage);
  const [status, setStatus] = useState<"" | "copied" | "failed">("");

  const draft = useMemo(() => buildComplaint({ date, caseSummary, amount, message }), [date, caseSummary, amount, message]);
  const [edited, setEdited] = useState<string | null>(null);
  const text = edited ?? draft;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setStatus("copied");
    } catch {
      setStatus("failed");
    }
    setTimeout(() => setStatus(""), 3000);
  };

  const field = "w-full rounded-xl border border-stone-300 bg-white px-3 py-3 text-base dark:border-stone-700 dark:bg-stone-900";
  const reset = () => setEdited(null);

  return (
    <section className="space-y-3 rounded-2xl border border-stone-200 p-4 dark:border-stone-800">
      <h3 className="text-lg font-bold">{ui.complaint_title[lang]}</h3>
      <p className="text-sm text-stone-600 dark:text-stone-400">🔒 {ui.complaint_privacy[lang]}</p>

      <label className="block space-y-1 text-sm font-medium">
        {ui.field_date[lang]}
        <input type="date" value={date} max={today} onChange={(e) => { setDate(e.target.value); reset(); }} className={field} />
      </label>
      <label className="block space-y-1 text-sm font-medium">
        {ui.field_amount[lang]}
        <input inputMode="numeric" value={amount} onChange={(e) => { setAmount(e.target.value); reset(); }} className={field} autoComplete="off" />
      </label>
      <label className="block space-y-1 text-sm font-medium">
        {ui.field_message[lang]}
        <textarea rows={4} value={message} onChange={(e) => { setMessage(e.target.value); reset(); }} className={field} autoComplete="off" spellCheck={false} />
      </label>

      <label className="block space-y-1 text-sm font-medium">
        {ui.draft_label[lang]}
        <textarea rows={12} value={text} onChange={(e) => setEdited(e.target.value)} className={`${field} font-mono text-sm`} spellCheck={false} />
      </label>

      <button onClick={copy} className="w-full rounded-2xl bg-teal-700 py-4 text-lg font-bold text-white active:bg-teal-800">
        {status === "copied" ? `✓ ${ui.copied[lang]}` : ui.copy[lang]}
      </button>
      {status === "failed" && <p role="alert" className="text-sm text-stone-700 dark:text-stone-300">{ui.copy_failed[lang]}</p>}
    </section>
  );
}
