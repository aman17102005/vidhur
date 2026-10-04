import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app.ai.adapters as adapters
from app.main import app

client = TestClient(app)
KEY = "sk-test-SECRET-1234567890"


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_analyze_and_url_validation():
    r = client.post("/analyze", json={"content": "share your otp", "mode": "text"})
    assert r.status_code == 200 and r.json()["verdict"] == "high_risk"
    assert client.post("/analyze", json={"content": "hello there", "mode": "url"}).status_code == 422


def test_validation_error_does_not_echo_key():
    r = client.post("/explain", json={"provider": "nope", "api_key": KEY, "content": "x", "verdict": "safe", "findings": []})
    assert r.status_code == 422 and KEY not in r.text


def test_explain_uses_adapter_and_never_returns_key(monkeypatch):
    seen = {}

    async def fake_post(url, headers, body):
        seen.update(url=url, headers=headers)
        return {"content": [{"type": "text", "text": "Looks risky because it asks for OTP."}]}

    monkeypatch.setattr(adapters, "_post", fake_post)
    r = client.post("/explain", json={"provider": "anthropic", "api_key": KEY, "content": "share otp", "verdict": "high_risk",
                                      "findings": [{"id": "ask_otp", "severity": "high", "reason": "asks otp"}]})
    assert r.status_code == 200 and "risky" in r.json()["explanation"]
    assert KEY not in r.text and seen["headers"]["x-api-key"] == KEY and KEY not in seen["url"]


def test_gemini_key_in_header_not_url(monkeypatch):
    seen = {}

    async def fake_post(url, headers, body):
        seen.update(url=url, headers=headers)
        return {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}

    monkeypatch.setattr(adapters, "_post", fake_post)
    r = client.post("/explain", json={"provider": "gemini", "api_key": KEY, "content": "x", "verdict": "safe", "findings": []})
    assert r.status_code == 200 and KEY not in seen["url"] and seen["headers"]["x-goog-api-key"] == KEY


def test_provider_error_is_sanitised(monkeypatch):
    import httpx

    class FakeResp:
        status_code = 401
        text = f"Incorrect API key provided: {KEY}"

        def json(self):
            return {}

    class FakeClient:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def post(self, *a, **k): return FakeResp()

    monkeypatch.setattr(adapters.httpx, "AsyncClient", FakeClient)
    r = client.post("/explain", json={"provider": "openai", "api_key": KEY, "content": "x", "verdict": "safe", "findings": []})
    assert r.status_code == 502 and KEY not in r.text and "rejected" in r.json()["detail"]


def test_ocr_rejects_non_image_and_oversize():
    assert client.post("/ocr", content=b"abc", headers={"content-type": "text/plain"}).status_code == 415
    assert client.post("/ocr", content=b"x" * (9 * 1024 * 1024), headers={"content-type": "image/png"}).status_code in (413,)


def test_ocr_pipeline_in_memory(monkeypatch, tmp_path):
    """Run the OCR route with a fake `tesseract` and check no file is created from the upload."""
    import os, stat, tempfile
    fake = tmp_path / "bin"
    fake.mkdir()
    exe = fake / "tesseract"
    exe.write_text("#!/bin/sh\ncat >/dev/null\necho 'Share your OTP immediately'\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", str(fake) + os.pathsep + os.environ["PATH"])
    scratch = tmp_path / "tmpdir"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))

    buf = io.BytesIO()
    Image.new("RGB", (1200, 800), "white").save(buf, "PNG")
    r = client.post("/ocr", content=buf.getvalue(), headers={"content-type": "image/png"})
    assert r.status_code == 200, r.text
    assert r.json()["result"]["verdict"] == "high_risk"
    assert list(scratch.iterdir()) == []  # nothing written to the temp dir
