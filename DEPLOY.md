# Deploying WC2026 — backend on Render, frontend on Vercel

The app is two parts: a **read-only FastAPI service** (reads the committed 8.5 MB
DuckDB) and the **Next.js frontend**. Host the API on Render, the site on Vercel,
and point the site at the API.

## 1. Backend → Render (free)

The repo already contains everything Render needs: `render.yaml`,
`requirements-api.txt`, and `data/wc2026.duckdb`.

1. Push the repo to GitHub (it's at `github.com/medsahbi10/worldcup-2026-analytics`).
2. Go to **render.com → New → Blueprint**, connect the repo. Render reads
   `render.yaml` and creates the **wc2026-api** web service (free plan).
3. Click **Apply / Deploy**. First build takes ~2–4 min.
4. When live, note the URL, e.g. `https://wc2026-api.onrender.com`.
   Verify: open `https://wc2026-api.onrender.com/api/health` → `{"status":"ok"}`.

> Free-tier note: the service sleeps after ~15 min idle, so the first request
> after a nap is slow (~30–60 s cold start). Fine for a demo/portfolio.

## 2. Frontend → Vercel

1. Go to **vercel.com → Add New → Project**, import the same repo.
2. Set **Root Directory = `frontend`** (the Next app lives in a subfolder).
3. Add an environment variable:
   - `NEXT_PUBLIC_API_URL` = your Render URL (no trailing slash),
     e.g. `https://wc2026-api.onrender.com`
4. **Deploy.** Vercel auto-detects Next.js; no other config needed.

Every push to `main` then redeploys the frontend automatically.

## Notes
- CORS is already open (`allow_origins=["*"]`) so Vercel → Render calls work.
- Flags/jerseys/fonts are bundled in `frontend/public/brand` (no CDN needed).
- Player photos come from Transfermarkt URLs and may not always load — cosmetic.
- The fonts are licensed "Free for Personal Use" — fine for a portfolio, check
  before any commercial use.
