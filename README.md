# Vidhur: Check before you trust

Free scam checker for Indian college students: messages, links, QR codes and screenshots.

* **Rules first.** A deterministic rule engine produces the verdict (Safe / Suspicious / High Risk), the reasons, and a next step. No scores.
* **No database, no stored images.** Rules are static JSON in `backend/app/rules/data/`. Screenshots are processed in memory and discarded.
* **Optional BYOK AI.** The user's key lives only in their browser's localStorage and is used for one request at a time.
* **Never visits links.** The backend only studies the text of an address.

## Layout

```
backend/   FastAPI + rule engine + Tesseract OCR (Docker)    -> Render
frontend/  React + TypeScript + Vite + Tailwind               -> Vercel / Netlify
render.yaml  Render blueprint
```

## Run locally

```bash
# backend (needs Python 3.9+; install Tesseract only if you want screenshot OCR: brew install tesseract tesseract-lang)
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --port 8000 --no-access-log
.venv/bin/python -m pytest

# frontend (new terminal)
cd frontend && npm install && npm run dev      # http://localhost:5173
```

## Deploy for free

### 1. Push to GitHub
Create a GitHub repo and push this `vidhur/` folder as the repo root (so `backend/` and `frontend/` are at the top level).

### 2. Backend on Render (free, Docker)
1. Sign up at render.com with GitHub (no card needed for the free web service).
2. **New +  ->  Blueprint**, pick your repo. Render reads `render.yaml`. (Or: **New + -> Web Service**, Language **Docker**, Dockerfile Path `./backend/Dockerfile`, Docker Build Context `./backend`, Instance Type **Free**, Health Check Path `/health`.)
3. Set the environment variable `ALLOWED_ORIGINS` to your frontend URL (you can add it after step 3, then redeploy), e.g. `https://vidhur.vercel.app`. Separate several origins with commas.
4. Deploy. The first build takes a few minutes (it installs Tesseract). Copy the service URL, e.g. `https://vidhur-api.onrender.com`.
5. Check `https://<your-service>.onrender.com/health` returns `{"status":"ok"}`.

The free tier sleeps after ~15 minutes idle; the first request then takes up to a minute. The app shows a "Waking up the server…" message while that happens.

### 3. Frontend on Vercel (free)
1. vercel.com -> **Add New -> Project** -> import the repo.
2. **Root Directory:** `frontend`. Framework preset: **Vite** (auto-detected). Build command `npm run build`, output `dist`.
3. **Environment Variables:** `VITE_API_URL` = your Render URL (no trailing slash).
4. Deploy. Copy the Vercel URL, put it in Render's `ALLOWED_ORIGINS`, and redeploy the backend.

*Netlify alternative:* New site from Git -> base directory `frontend`, build command `npm run build`, publish directory `frontend/dist`, same `VITE_API_URL` variable.

### 4. Smoke test
Open the site on your phone, wait for the banner to clear, paste: `Your SBI account will be blocked. Update KYC at http://sbi-kyc-update.xyz` and expect **High Risk**. Then try a screenshot and a QR code.

## Optional: model names
Default models for the AI explanation are in `backend/app/ai/adapters.py` (override with env vars `VIDHUR_MODEL_OPENAI`, `VIDHUR_MODEL_ANTHROPIC`, `VIDHUR_MODEL_GEMINI`, `VIDHUR_MODEL_GROK`). Providers retire models, so if one stops working, change it there or type a model name under "Advanced" in the app's AI settings.

## Privacy design (what to preserve when changing code)
* `/ocr` takes the raw image as the request body and pipes it to the `tesseract` binary over stdin. Do not switch to multipart uploads or `pytesseract`: both write the image to a temp file on disk.
* Access logs are off (`--no-access-log`), validation errors do not echo input, and the `/explain` route never logs or returns the key. Keep it that way.
* QR images are decoded in the browser (`jsQR`) and never uploaded.
