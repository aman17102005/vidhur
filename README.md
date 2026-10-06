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

## Editing scam knowledge (no code needed)

Everything below is plain JSON. Edit, run the tests, push.

| File | What it holds |
|---|---|
| `backend/app/rules/data/phrases.json` | Phrase rules (English, Hinglish, Hindi). Each rule has an `id`, `severity`, `reason` and regex patterns. |
| `backend/app/rules/data/consequences.json` | Feature 1: what could happen if the user acts, per finding id. |
| `backend/app/rules/data/playbooks.json` | Feature 2: scam types and how they work. |
| `frontend/src/data/emergency.json` | Feature 3: emergency steps, phone numbers, URLs, wording. |

### Consequence preview
Under the reasons, Suspicious and High Risk results show up to 3 lines under **"What could happen if you go ahead"**, most serious first, in the language of the message (English, Hindi or Hinglish). Safe results show nothing. To add one, add the finding id to `consequences` with `severity` (`high` or `medium`) and `en`, `hi`, `hinglish` text. Use careful words ("can", "may", "usually"). If a new rule has no consequence, list its id under `no_consequence`; a test fails until you do one or the other.

### Scam playbook
When at least `PLAYBOOK_MIN_MATCHES` (2, in `backend/app/rules/playbooks.py`) of a playbook's `finding_ids` fire, the result shows a collapsed card "This looks like: <scam name>" with how it works, what they ask next, and what the real thing looks like. Only the best match is shown. `boost_terms` only break ties between playbooks. Never name a real company or person as the scammer. A new playbook needs a test message in `backend/tests/test_playbooks.py`.

### "I already paid / shared my OTP" help
A button on the main page opens a calm step-by-step screen: pick what happened, then follow a numbered checklist (English / हिंदी / Hinglish). It is bundled into the frontend, so it opens instantly even while the Render server is asleep. All numbers and links live in `emergency.json`:
* Only **1930** and **cybercrime.gov.in** are listed. They were checked against Press Information Bureau (Ministry of Home Affairs) material on `last_verified`. Bank numbers are deliberately not listed (they differ by bank): the screen tells the user to use the number on their card or passbook.
* When you re-check these, update `last_verified`. A test fails if an unexpected phone number appears in the file.
* The **complaint draft helper** builds its text in the browser only. It does not call the backend, does not use browser storage and does not log. Tests in `backend/tests/test_emergency.py` and `frontend/src/lib/complaint.test.ts` enforce this.

## Tests

```bash
cd backend && .venv/bin/python -m pytest      # rules, API, consequences, playbooks, emergency data
cd frontend && npm test                       # complaint draft + no-network guard
```

## Optional: model names
Default models for the AI explanation are in `backend/app/ai/adapters.py` (override with env vars `VIDHUR_MODEL_OPENAI`, `VIDHUR_MODEL_ANTHROPIC`, `VIDHUR_MODEL_GEMINI`, `VIDHUR_MODEL_GROK`). Providers retire models, so if one stops working, change it there or type a model name under "Advanced" in the app's AI settings.

## Privacy design (what to preserve when changing code)
* `/ocr` takes the raw image as the request body and pipes it to the `tesseract` binary over stdin. Do not switch to multipart uploads or `pytesseract`: both write the image to a temp file on disk.
* Access logs are off (`--no-access-log`), validation errors do not echo input, and the `/explain` route never logs or returns the key. Keep it that way.
* QR images are decoded in the browser (`jsQR`) and never uploaded.
