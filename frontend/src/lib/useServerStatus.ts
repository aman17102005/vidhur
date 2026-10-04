import { useCallback, useEffect, useRef, useState } from "react";
import { health } from "./api";

export type ServerStatus = "checking" | "waking" | "ready" | "offline";

const GIVE_UP_MS = 120_000;

// Render's free tier sleeps when idle. Ping /health on load and keep retrying until it answers,
// so the first real request never silently hangs.
export function useServerStatus() {
  const [status, setStatus] = useState<ServerStatus>("checking");
  const [attempt, setAttempt] = useState(0);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    setStatus("checking");
    const started = Date.now();
    const wakeTimer = setTimeout(() => !cancelled.current && setStatus((s) => (s === "checking" ? "waking" : s)), 1500);

    (async () => {
      while (!cancelled.current) {
        try {
          await health();
          if (!cancelled.current) setStatus("ready");
          return;
        } catch {
          if (Date.now() - started > GIVE_UP_MS) {
            if (!cancelled.current) setStatus("offline");
            return;
          }
          await new Promise((r) => setTimeout(r, 3000));
        }
      }
    })();

    return () => {
      cancelled.current = true;
      clearTimeout(wakeTimer);
    };
  }, [attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { status, retry };
}
