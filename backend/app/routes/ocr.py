from fastapi import APIRouter, HTTPException, Request

from ..models import OcrResponse
from ..ocr import MAX_UPLOAD_BYTES, OcrError, extract_text
from ..rules.engine import analyze

router = APIRouter()


@router.post("/ocr", response_model=OcrResponse)
async def ocr_route(request: Request) -> OcrResponse:
    # The browser sends the raw image bytes as the request body (not multipart/form-data).
    # Multipart parsing spools uploads over 1 MB to a temp file on disk; reading the
    # body stream ourselves keeps the image purely in memory.
    if not (request.headers.get("content-type", "")).startswith("image/"):
        raise HTTPException(415, "Send the screenshot as an image.")
    buf = bytearray()
    async for chunk in request.stream():
        buf += chunk
        if len(buf) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Image is too large (max 8 MB).")
    data = bytes(buf)
    buf.clear()
    try:
        text = await extract_text(data)
    except OcrError as e:
        raise HTTPException(422, str(e))
    finally:
        del data
    return OcrResponse(text=text, result=analyze(text))
