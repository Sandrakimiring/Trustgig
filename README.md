# TrustGig

**AI-assisted freelance marketplace for Kenya** — semantic job-to-freelancer matching (sentence embeddings + FAISS), SMS notifications (Africa’s Talking), escrow-style job flow, M-Pesa disbursement hooks, and OpenAI-powered coaching and explanations.

---

## Live demo

**Frontend (production):** [https://trustgig-frontend.onrender.com/](https://trustgig-frontend.onrender.com/)

Open the app in your browser to explore the client and freelancer flows against the deployed backend services.

---

## Walkthrough videos (Loom)

Recorded as **separate sessions** (not a single split-screen run). In an ideal demo, **client and freelancer would run side by side** — e.g. client posts a gig while a freelancer applies — so you can follow the full loop in real time.

| Flow | Link | Notes |
|------|------|--------|
| **Client** | [Watch on Loom — client walkthrough](https://www.loom.com/share/46138c37800c403692d95fd848ea810e?utm_medium=gif) | Shows posting and client-side usage |
| **Freelancer** | [Watch on Loom — freelancer walkthrough](https://www.loom.com/share/31a80e3c436d4c4fb89a81768dc94353) | **Older UI** in this recording; behavior is the same idea, but the **current** live site matches the polished frontend linked above |

---

## What’s in this repo

| Piece | Role |
|--------|------|
| **`frontend/`** | Single-page HTML/CSS/JS client (dark/light theme, client vs freelancer views) |
| **`backend/app/`** | Main **FastAPI** API: auth, jobs, applications, escrow, deliveries, SMS triggers; calls the matcher over HTTP |
| **`trustgig/`** | **Matching microservice**: `SentenceTransformer` + **FAISS** retrieval, reliability + budget scoring (`matcher.py`, `scorer.py`, `embedder.py`) |
| **`backend/app/ai_routes/`** | **`/ai`** routes: OpenAI (`gpt-4o-mini`) for job rewrites, profile coaching, match explanations, trust narratives, review analysis |

Deployed setup (see comments in `backend/app/main.py`) commonly splits:

- **Frontend** — static host (e.g. Render)  
- **Platform API** — backend service  
- **Matcher** — ML service URL configured via `MATCHER_SERVICE_URL`

---

## Features

- **Semantic matching** — `all-MiniLM-L6-v2` embeddings, FAISS top-K search, then weighted score (skill fit, completion/reliancy, budget fit).
- **Job lifecycle** — open → fund escrow / assign freelancer → deliver → approve or reject → completion and payment notification paths.
- **SMS** — match alerts, application notices, escrow and delivery messages (Africa’s Talking).
- **Payments** — M-Pesa disbursement helpers on approval/release paths (configure sandbox/production credentials).
- **AI helpers** — optional OpenAI features under **`/ai`** (requires `OPENAI_API_KEY`).

---

## Tech stack

- **API:** FastAPI, Uvicorn, HTTPX  
- **Data:** SQLAlchemy, PostgreSQL (recommended in production) or SQLite for local dev  
- **ML:** sentence-transformers, FAISS, PyTorch (CPU wheels in `requirements.txt`), scikit-learn  
- **Integrations:** Africa’s Talking (SMS / payments SDK), OpenAI Python SDK  
- **Frontend:** Static HTML + vanilla JS (no build step)

---

## Repository layout (actual)

```
├── backend/app/          # Platform API (main.py, models, database, services, ai_routes)
├── frontend/             # index.html + assets for static hosting
├── trustgig/             # Matching service package (main.py, embedder, matcher, scorer, models)
├── docs/                 # MkDocs material
├── migrate.py            # DB migration helpers
├── seed_data.py          # Sample data (root + backend variants if present)
├── download_model.py     # Pre-download embedding model for faster startup
├── requirements.txt
├── pyproject.toml
└── .env.example
```

Legacy / supplemental: `backend/app/services/vectorizer.py` (older keyword-style similarity), root `ai_routes/` script-style experiments — not the primary FastAPI AI surface (`backend/app/ai_routes/`).

---

## Quick start (local)

**1. Clone and install**

```bash
git clone https://github.com/Sandrakimiring/Trustgig.git
cd Trustgig
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL, API keys, URLs
```

**2. Optional: cache the embedding model**

```bash
python download_model.py
```

**3. Run the platform API** (imports assume `backend/app` as the app root)

```bash
cd backend/app
uvicorn main:app --reload --port 8000
```

- API root: [http://localhost:8000](http://localhost:8000)  
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

**4. Run the matcher service** (separate terminal, from repo root)

```bash
uvicorn trustgig.main:app --reload --port 8001
```

Point the backend at it:

```env
MATCHER_SERVICE_URL=http://127.0.0.1:8001
```

**5. Open the frontend**

Serve `frontend/` with any static server (or open `frontend/index.html` with your API base URL configured in the client script as appropriate for local testing).

---

## Configuration

Copy [`.env.example`](.env.example) to `.env`. Typical variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy URL (SQLite locally, Postgres in production) |
| `MATCHER_SERVICE_URL` | Base URL of the matching service |
| `FRONTEND_URL` | Used in SMS links back to the web app |
| Africa’s Talking (`AT_USERNAME`, `AT_API_KEY`, etc.) | SMS and payment integration |
| `OPENAI_API_KEY` | `/ai` features |

---

## Database

```bash
python migrate.py     # apply additive fixes / compatibility updates
python seed_data.py   # optional sample users/jobs
```

---

## ML matching (high level)

1. Job skills and budget are sent to **`POST /match`** on the matcher service.  
2. Freelancer skill text is embedded with **MiniLM**; **FAISS** returns top candidates by cosine similarity (inner product on normalized vectors).  
3. **Final score** blends vector similarity, reliability (completion rate × recency), and budget fit — see `trustgig/matcher.py` and `trustgig/scorer.py`.

---

## Testing and scripts

```bash
pytest
pytest test_embedder.py
python test_endpoint_local.py
```

The root **Makefile** may reference optional Cookiecutter-era modules (`trustgig.dataset`, etc.); use the commands above if those entrypoints are missing in your checkout.

---

## Contributing

1. Match existing style (Black / isort settings in `pyproject.toml` where applicable).  
2. Run tests and lint before opening a PR.  
3. Keep README and `.env.example` in sync when adding services or env vars.

---

## License

MIT — see [LICENSE](LICENSE).
