import { useEffect, useState } from "react";

interface Props {
  disabled: boolean;
  onFile: (file: File) => void;
  fileName: string;
}

export default function ScreenshotInput({ disabled, onFile, fileName }: Props) {
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const pick = (file?: File) => {
    if (!file) return;
    setPreview(URL.createObjectURL(file)); // lives only in this tab's memory
    onFile(file);
  };

  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const f = Array.from(e.clipboardData?.files ?? []).find((x) => x.type.startsWith("image/"));
      if (f && !disabled) pick(f);
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  });

  return (
    <div className="space-y-3">
      <label className={`flex min-h-32 cursor-pointer flex-col items-center justify-center gap-1 rounded-2xl border-2 border-dashed border-stone-300 p-4 text-center dark:border-stone-700 ${disabled ? "opacity-50" : ""}`}>
        {preview ? (
          <img src={preview} alt="Your screenshot" className="max-h-56 rounded-lg object-contain" />
        ) : (
          <>
            <span className="text-3xl">📱</span>
            <span className="font-semibold">Tap to choose a screenshot</span>
            <span className="text-xs text-stone-500">or paste one (Ctrl+V)</span>
          </>
        )}
        <input type="file" accept="image/*" disabled={disabled} className="sr-only" onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ""; }} />
      </label>
      {fileName && <p className="truncate text-xs text-stone-500">{fileName}</p>}
      <p className="text-xs text-stone-500 dark:text-stone-400">🔒 Your screenshot is read once to pull out the text, then thrown away. It is never saved on disk or in a database.</p>
    </div>
  );
}
