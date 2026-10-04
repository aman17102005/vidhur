"""Screenshot -> text, entirely in memory.

pytesseract writes every image to a temp file on disk, which would break the
"never write uploads to disk" rule. Instead we pipe PNG bytes into the
`tesseract` binary over stdin and read text from stdout. No file is created.
"""
import asyncio
import io
import os
import shutil

from PIL import Image, ImageOps

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_SIDE = 2200
Image.MAX_IMAGE_PIXELS = 40_000_000  # decompression-bomb guard
OCR_LANGS = os.getenv("OCR_LANGS", "eng+hin")
OCR_TIMEOUT_S = 40

# Free tier has ~512 MB RAM: one OCR job at a time.
_slot = asyncio.Semaphore(1)


class OcrError(Exception):
    pass


def _prepare(data: bytes) -> bytes:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        raise OcrError("That file could not be read as an image.")
    img = ImageOps.exif_transpose(img).convert("L")  # grayscale also drops EXIF/location
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE))
    elif max(img.size) < 1000:
        img = img.resize((img.width * 2, img.height * 2))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def extract_text(data: bytes) -> str:
    if len(data) > MAX_UPLOAD_BYTES:
        raise OcrError("Image is too large (max 8 MB).")
    if not shutil.which("tesseract"):
        raise OcrError("Text reading is not available on this server right now.")
    png = _prepare(data)
    del data
    async with _slot:
        proc = await asyncio.create_subprocess_exec(
            "tesseract", "stdin", "stdout", "-l", OCR_LANGS, "--psm", "6",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(png), timeout=OCR_TIMEOUT_S)
        except asyncio.TimeoutError:
            proc.kill()
            raise OcrError("Reading the screenshot took too long. Try a smaller or cropped image.")
        finally:
            del png
    text = out.decode("utf-8", errors="ignore").strip()
    if not text:
        raise OcrError("No readable text found in the image.")
    return text
