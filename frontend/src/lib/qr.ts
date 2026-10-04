import jsQR from "jsqr";

// QR decoding happens entirely in the browser. The image never leaves the device.

function decodeCanvas(ctx: CanvasRenderingContext2D, w: number, h: number): string | null {
  const data = ctx.getImageData(0, 0, w, h);
  return jsQR(data.data, w, h, { inversionAttempts: "attemptBoth" })?.data ?? null;
}

export async function decodeQrFromFile(file: File): Promise<string | null> {
  const bitmap = await createImageBitmap(file);
  try {
    for (const maxSide of [1200, 700, 2000]) {
      const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
      const w = Math.max(1, Math.round(bitmap.width * scale));
      const h = Math.max(1, Math.round(bitmap.height * scale));
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      if (!ctx) return null;
      ctx.drawImage(bitmap, 0, 0, w, h);
      const text = decodeCanvas(ctx, w, h);
      if (text) return text;
    }
    return null;
  } finally {
    bitmap.close();
  }
}

export function decodeVideoFrame(video: HTMLVideoElement, canvas: HTMLCanvasElement): string | null {
  const w = video.videoWidth;
  const h = video.videoHeight;
  if (!w || !h) return null;
  const scale = Math.min(1, 800 / Math.max(w, h));
  canvas.width = Math.round(w * scale);
  canvas.height = Math.round(h * scale);
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) return null;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  return decodeCanvas(ctx, canvas.width, canvas.height);
}
