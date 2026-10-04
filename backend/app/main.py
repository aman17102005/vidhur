import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .ocr import MAX_UPLOAD_BYTES
from .routes import analyze, explain, ocr

# Privacy: nothing request-related is ever logged. Silence access logs and keep the root logger quiet.
logging.getLogger("uvicorn.access").disabled = True
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)
logging.getLogger().setLevel(logging.WARNING)

app = FastAPI(title="Vidhur", docs_url=None, redoc_url=None, openapi_url=None)

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"], allow_credentials=False)


@app.middleware("http")
async def limit_body(request: Request, call_next):
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_UPLOAD_BYTES + 64 * 1024:
        return JSONResponse({"detail": "Request too large."}, status_code=413)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, __: RequestValidationError):
    # Default handler echoes the submitted input (which may include an API key). Return a generic message instead.
    return JSONResponse({"detail": "That request was not valid. Check the text length and try again."}, status_code=422)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(analyze.router)
app.include_router(ocr.router)
app.include_router(explain.router)
