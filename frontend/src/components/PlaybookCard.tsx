import type { Lang, Playbook } from "../types";

const HEADINGS: Record<Lang, { looksLike: string; how: string; next: string; real: string }> = {
  en: { looksLike: "This looks like", how: "How this scam works", next: "What they will ask next", real: "What the real thing looks like" },
  hi: { looksLike: "यह ऐसा लगता है", how: "यह स्कैम कैसे काम करता है", next: "वे आगे क्या माँगेंगे", real: "असली चीज़ कैसी होती है" },
  hinglish: { looksLike: "Yeh aisa lagta hai", how: "Yeh scam kaise kaam karta hai", next: "Woh aage kya maangenge", real: "Asli cheez kaisi hoti hai" },
};

export default function PlaybookCard({ playbook, lang }: { playbook: Playbook; lang: Lang }) {
  const h = HEADINGS[lang] ?? HEADINGS.en;
  return (
    <details className="group rounded-2xl border border-stone-200 bg-white p-4 dark:border-stone-800 dark:bg-stone-900">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-2 font-semibold">
        <span>
          <span className="block text-xs font-medium uppercase tracking-wide text-stone-500">{h.looksLike}</span>
          {playbook.name}
        </span>
        <span aria-hidden className="text-stone-400 transition group-open:rotate-180">▾</span>
      </summary>
      <div className="mt-3 space-y-4 text-sm">
        <Section title={h.how} items={playbook.how_it_works} numbered />
        <Section title={h.next} items={playbook.what_next} />
        <Section title={h.real} items={playbook.real_looks_like} />
      </div>
    </details>
  );
}

function Section({ title, items, numbered = false }: { title: string; items: string[]; numbered?: boolean }) {
  const List = numbered ? "ol" : "ul";
  return (
    <div>
      <h4 className="mb-1 font-semibold text-stone-700 dark:text-stone-300">{title}</h4>
      <List className={`space-y-1 pl-5 ${numbered ? "list-decimal" : "list-disc"}`}>
        {items.map((t, i) => (
          <li key={i}>{t}</li>
        ))}
      </List>
    </div>
  );
}
