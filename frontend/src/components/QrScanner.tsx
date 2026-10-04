import { useEffect, useRef, useState } from "react";
import { decodeQrFromFile, decodeVideoFrame } from "../lib/qr";

interface Props {
  disabled: boolean;
  onDecoded: (text: string) => void;
}

export default function QrScanner({ disabled, onDecoded }: Props) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(document.createElement("canvas"));
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef(0);

  const stop = () => {
    cancelAnimationFrame(rafRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setScanning(false);
  };

  useEffect(() => stop, []);

  const start = async () => {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia) return setError("Camera is not available here. Upload a QR image instead.");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      streamRef.current = stream;
      setScanning(true);
      // wait for <video> to mount
      requestAnimationFrame(async () => {
        const v = videoRef.current;
        if (!v) return;
        v.srcObject = stream;
        await v.play().catch(() => {});
        let last = 0;
        const tick = (t: number) => {
          if (!streamRef.current) return;
          if (t - last > 150) {
            last = t;
            const text = decodeVideoFrame(v, canvasRef.current);
            if (text) {
              stop();
              onDecoded(text);
              return;
            }
          }
          rafRef.current = requestAnimationFrame(tick);
        };
        rafRef.current = requestAnimationFrame(tick);
      });
    } catch {
      setError("Could not open the camera. Allow camera access, or upload a QR image instead.");
    }
  };

  const onFile = async (file?: File) => {
    if (!file) return;
    setError("");
    try {
      const text = await decodeQrFromFile(file);
      if (text) onDecoded(text);
      else setError("No QR code found in that image. Try a clearer, closer picture.");
    } catch {
      setError("That file could not be read as an image.");
    }
  };

  return (
    <div className="space-y-3">
      {scanning ? (
        <div className="space-y-3">
          <div className="relative overflow-hidden rounded-2xl bg-black">
            <video ref={videoRef} playsInline muted className="aspect-square w-full object-cover" />
            <div className="pointer-events-none absolute inset-8 rounded-2xl border-4 border-white/70" />
          </div>
          <button onClick={stop} className="w-full rounded-xl border border-stone-300 py-3 font-medium dark:border-stone-700">Cancel</button>
        </div>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2">
          <button disabled={disabled} onClick={start} className="rounded-xl bg-teal-700 py-3 font-semibold text-white disabled:opacity-50 active:bg-teal-800">📷 Scan with camera</button>
          <label className={`cursor-pointer rounded-xl border border-stone-300 py-3 text-center font-semibold dark:border-stone-700 ${disabled ? "opacity-50" : ""}`}>
            🖼️ Upload QR image
            <input type="file" accept="image/*" disabled={disabled} className="sr-only" onChange={(e) => { onFile(e.target.files?.[0]); e.target.value = ""; }} />
          </label>
        </div>
      )}
      <p className="text-xs text-stone-500 dark:text-stone-400">🔒 The QR is read on your phone. Only the text or link inside it is checked. The picture is never uploaded.</p>
      {error && <p role="alert" className="text-sm text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
