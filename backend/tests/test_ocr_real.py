"""Runs the real tesseract binary. Skipped automatically when it is not installed."""
import io
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from app.main import app

pytestmark = pytest.mark.skipif(not shutil.which("tesseract"), reason="tesseract not installed")
client = TestClient(app)


def _screenshot(text: str, noisy: bool = False) -> bytes:
    import os
    img = Image.new("RGB", (1080, 2400), "white")
    if noisy:  # poorly compressible, so the PNG is well over 1 MB
        img = Image.frombytes("RGB", (1080, 2400), os.urandom(1080 * 2400 * 3)).point(lambda v: 215 + v // 8)
    d = ImageDraw.Draw(img)
    d.rectangle((40, 150, 1040, 330), fill="white")
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 44)
    except OSError:
        font = ImageFont.truetype("DejaVuSans.ttf", 44)
    d.text((60, 180), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _files_in_tmp():
    return {p for p in Path(tempfile.gettempdir()).rglob("*") if p.is_file()}


@pytest.mark.parametrize("noisy", [False, True], ids=["small", "over-1MB"])
def test_real_ocr_catches_hinglish_scam_and_writes_nothing(noisy):
    png = _screenshot("Turant paise bhejo. OTP batao jaldi.", noisy)
    if noisy:
        assert len(png) > 1_000_000
    before = _files_in_tmp()
    r = client.post("/ocr", content=png, headers={"content-type": "image/png"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "paise" in body["text"].lower()
    ids = {f["id"] for f in body["result"]["findings"]}
    assert {"ask_otp", "money_request_hinglish"} <= ids
    assert body["result"]["verdict"] == "high_risk"
    assert _files_in_tmp() - before == set()
