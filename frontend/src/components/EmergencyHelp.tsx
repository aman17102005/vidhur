import { useState } from "react";
import emergency from "../data/emergency.json";
import type { Lang } from "../types";
import ComplaintHelper from "./ComplaintHelper";

type CaseId = keyof typeof emergency.cases;
type StepId = keyof typeof emergency.steps;

const CASE_SUMMARY: Record<CaseId, string> = {
  paid: "I paid money to a person or website after being misled by a message, call or link.",
  otp: "I shared an OTP or PIN with a person who contacted me.",
  link: "I clicked a suspicious link or installed an app that I was sent.",
  details: "I shared my bank, card or ID details with a person who contacted me.",
};

interface Props {
  initialLang: Lang;
  initialMessage: string;
  onBack: () => void;
}

// Works without the backend: all content is bundled, so it opens instantly even while the server is asleep.
export default function EmergencyHelp({ initialLang, initialMessage, onBack }: Props) {
  const [lang, setLang] = useState<Lang>(initialLang);
  const [chosen, setChosen] = useState<CaseId | null>(null);
  const ui = emergency.ui;
  const { helpline, portal } = emergency.contacts;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-2">
        <button onClick={onBack} className="-ml-2 rounded-lg px-2 py-2 text-sm font-medium text-teal-800 dark:text-teal-300">← {ui.back[lang]}</button>
        <div role="group" aria-label="Language" className="flex rounded-xl bg-stone-200 p-1 dark:bg-stone-800">
          {emergency.languages.map((l) => (
            <button
              key={l.code}
              onClick={() => setLang(l.code as Lang)}
              aria-pressed={lang === l.code}
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${lang === l.code ? "bg-white shadow dark:bg-stone-950" : "text-stone-600 dark:text-stone-400"}`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <header className="space-y-2">
        <h2 className="text-2xl font-extrabold">{ui.title[lang]}</h2>
        <p className="text-stone-700 dark:text-stone-300">{ui.calm[lang]}</p>
      </header>

      {!chosen ? (
        <section className="space-y-3">
          <h3 className="text-lg font-bold">{ui.question[lang]}</h3>
          <p className="text-sm text-stone-600 dark:text-stone-400">{ui.pick_closest[lang]}</p>
          <div className="grid gap-3">
            {(Object.keys(emergency.cases) as CaseId[]).map((id) => (
              <button
                key={id}
                onClick={() => setChosen(id)}
                className="min-h-16 rounded-2xl border-2 border-stone-300 bg-white px-4 py-4 text-left text-lg font-semibold active:bg-stone-100 dark:border-stone-700 dark:bg-stone-900 dark:active:bg-stone-800"
              >
                {emergency.cases[id].title[lang]}
              </button>
            ))}
          </div>
        </section>
      ) : (
        <section className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-lg font-bold">{emergency.cases[chosen].title[lang]}</h3>
            <button onClick={() => setChosen(null)} className="shrink-0 text-sm font-medium text-teal-800 underline dark:text-teal-300">{ui.change_answer[lang]}</button>
          </div>

          <div className="grid gap-2 sm:grid-cols-2">
            <a href={helpline.tel} className="rounded-2xl bg-teal-700 py-4 text-center text-lg font-bold text-white active:bg-teal-800">📞 {ui.call_now[lang]}</a>
            <a href={portal.url} target="_blank" rel="noopener noreferrer" className="rounded-2xl border-2 border-teal-700 py-4 text-center text-lg font-bold text-teal-800 dark:text-teal-300">{ui.open_portal[lang]}</a>
          </div>

          <h3 className="pt-2 text-lg font-bold">{ui.checklist[lang]}</h3>
          <ol className="space-y-3">
            {emergency.cases[chosen].steps.map((sid, i) => (
              <li key={sid} className="flex gap-3 rounded-2xl bg-white p-4 dark:bg-stone-900">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-teal-700 font-bold text-white" aria-hidden>{i + 1}</span>
                <span className="pt-0.5">{emergency.steps[sid as StepId][lang]}</span>
              </li>
            ))}
          </ol>
          <p className="text-sm text-stone-600 dark:text-stone-400">{emergency.bank_note[lang]}</p>

          <ComplaintHelper lang={lang} caseSummary={CASE_SUMMARY[chosen]} initialMessage={initialMessage} />
        </section>
      )}

      <footer className="space-y-1 rounded-2xl bg-stone-100 p-4 text-sm text-stone-700 dark:bg-stone-900 dark:text-stone-300">
        <p className="font-semibold">{emergency.disclaimer[lang]}</p>
        <p className="text-xs text-stone-500">{ui.last_checked[lang]}: {emergency.last_verified}</p>
      </footer>
    </div>
  );
}
