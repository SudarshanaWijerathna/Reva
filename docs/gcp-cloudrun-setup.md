# Google Cloud Run Setup Guide — Reva Backend

Deploy the Reva backend to **Google Cloud Run** for a fully serverless, highly available backend.

---

## 🌟 Why Google Cloud Run?

| Feature | Benefit |
|---|---|
| **Free Quota** | 360,000 GiB-seconds RAM + 2 Million requests free per month |
| **HTTPS Built-in** | Provides an `https://...a.run.app` URL out of the box (zero domain needed!) |
| **No Capacity Issues** | Deploys instantly without "Out of capacity" errors |
| **Zero Cold Cost** | Scales to 0 when idle ($0 cost) |
| **Vercel Ready** | `https://reva-front.vercel.app` can call the Cloud Run URL directly |

---

## 📋 Prerequisites

1. A **Google Cloud Account** ([console.cloud.google.com](https://console.cloud.google.com)) — get $300 free credits upon sign-up.
2. Google Cloud SDK (`gcloud` CLI) installed locally **OR** use **Google Cloud Shell** (built directly into the browser — no local installation needed!).

---

## ⚠️ Important — First Build is Slow

The Reva backend has a large dependency footprint (TensorFlow, PyTorch, CatBoost, ChromaDB, etc.). Expect:

| Step | Time estimate |
|---|---|
| First Cloud Build (image build) | **15–25 minutes** |
| Subsequent builds (layer cache) | **5–8 minutes** |
| Container startup (model loading) | **45–90 seconds** (cold start) |
| Container startup (warm instance) | **< 1 second** |

This is completely normal. Set `--min-instances 1` if you want to eliminate cold starts (at a small cost).

---

## 🚀 Deployment Methods

Choose **Method A** (automated script — recommended), **Method B** (one-liner in Cloud Shell), or **Method C** (browser UI).

---

## 🎯 Method A — Automated Deploy Script (Recommended)

A pre-built script at `scripts/deploy_cloudrun.sh` handles everything: API enablement, deploy, secret injection, and health check.

### Step 1: (Optional) Pre-fill your secrets

```bash
cp .env.example .env.cloudrun
# Edit .env.cloudrun with your real values — this file is git-ignored
```

### Step 2: Run the script

**In Google Cloud Shell (browser):**
```bash
git clone https://github.com/SudarshanaWijerathna/Reva.git
cd Reva
bash scripts/deploy_cloudrun.sh
```

**Locally (if `gcloud` is installed and authenticated):**
```bash
cd /path/to/Reva
bash scripts/deploy_cloudrun.sh
```

The script will:
1. ✅ Verify `gcloud` auth and active project
2. ✅ Enable Cloud Run / Cloud Build / Artifact Registry APIs
3. ✅ Build and deploy via `gcloud run deploy --source .`
4. ✅ Prompt for secrets and apply them
5. ✅ Run a `/health` check and print the live URL

---

## 🖥️ Method B — 1-Command Deploy via Cloud Shell

### Step 1: Open Cloud Shell

1. Go to [console.cloud.google.com](https://console.cloud.google.com).
2. Click the **Activate Cloud Shell** icon `[>_]` in the top right header bar.
3. A terminal window will open at the bottom of your browser screen.

### Step 2: Clone Repo & Deploy

```bash
# 1. Clone the repository
git clone https://github.com/SudarshanaWijerathna/Reva.git
cd Reva

# 2. Deploy directly to Cloud Run
gcloud run deploy reva-backend \
  --source . \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 3 \
  --port 8000 \
  --timeout 300 \
  --concurrency 10 \
  --set-env-vars "ENABLE_SCHEDULER=false,MODEL_RUNTIME_MODE=embedded,PORTFOLIO_VALUATION_ENGINE=legacy,CORS_ORIGINS=https://reva-front.vercel.app"
```

> **Note:** Replace `asia-southeast1` (Singapore) with `us-central1` if preferred.

### Step 3: Add Your Secrets (Environment Variables)

After deployment, gcloud will print your live **Service URL** (e.g., `https://reva-backend-xyz-as.a.run.app`).

```bash
gcloud run services update reva-backend \
  --region asia-southeast1 \
  --update-env-vars "DATABASE_URL=postgresql+psycopg2://username:password@host:5432/reva?sslmode=require,SECRET_KEY=your_secret_key,GEMINI_API_KEY=your_gemini_key,NEWS_API=your_news_key,DB_LINK=your_mongo_url"
```

> 💡 **Better approach:** Use GCP Secret Manager to keep secrets out of revision history. See [`docs/gcp-secrets-setup.md`](./gcp-secrets-setup.md).

---

## 🖱️ Method C — Deploy via GCP Console Web UI

If you prefer using the browser web interface:

1. In GCP Console, search for **Cloud Run** → click **Create Service**.
2. Select **Deploy one revision from an existing container image** or **Continuously deploy from a repository** (Connect to GitHub).
3. **Service name:** `reva-backend`
4. **Region:** `asia-southeast1 (Singapore)` or `us-central1 (Iowa)`.
5. **Authentication:** Select **Allow unauthenticated invocations**.
6. Under **Container, Networking, Security**:
   - **Container Port:** `8000`
   - **Memory:** `4 GiB`
   - **CPU:** `2`
   - **Request timeout:** `300s`
   - **Environment variables:** Add `DATABASE_URL`, `GEMINI_API_KEY`, `SECRET_KEY`, `CORS_ORIGINS=https://reva-front.vercel.app`.
7. Click **Create**!

---

## 🔗 Connect Your Vercel Frontend

1. Copy your live Cloud Run HTTPS URL (e.g. `https://reva-backend-xxxx-as.a.run.app`).
2. Test it: `https://reva-backend-xxxx-as.a.run.app/health` → should return `{"status":"ok"}` or `{"status":"healthy"}`.
3. Go to [Vercel Dashboard](https://vercel.com) → **reva-front → Settings → Environment Variables**.
4. Set `VITE_API_BASE_URL` = `https://reva-backend-xxxx-as.a.run.app`
5. Go to **Deployments** → **Redeploy**.

---

## 🛠️ Database & Caching Options

### PostgreSQL
- **Option 1 (Existing):** Use your existing Azure Postgres URL in `DATABASE_URL`.
- **Option 2 (Free Cloud Postgres):** Create a free serverless PostgreSQL on [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com).

### Redis (Optional)
- If omitted, Reva computes sentiment on-demand (slower but works).
- For free cloud Redis: [Upstash Redis](https://upstash.com) (10,000 requests/day free).
- Connection string format: `REDIS_URL=rediss://username:password@host:port`

---

## 🔁 GitHub Actions CI/CD (Automatic Deploy on Push)

For continuous deployment — every push to `main` automatically builds and deploys to Cloud Run:

### Step 1: Create a Service Account for CI

```bash
PROJECT_ID=$(gcloud config get-value project)

gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Cloud Run Deployer"

# Grant required roles
for ROLE in roles/run.admin roles/cloudbuild.builds.editor roles/storage.admin roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="$ROLE" --quiet
done

# Export key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account="github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com"
```

### Step 2: Add GitHub Secrets

In your GitHub repo → **Settings → Secrets → Actions**, add:
- `GCP_PROJECT_ID` — your project ID
- `GCP_SA_KEY` — contents of `github-actions-key.json` (then delete the file!)

### Step 3: Create the workflow

Create `.github/workflows/deploy-backend.yml`:

```yaml
name: Deploy Backend to Cloud Run

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - 'ml/**'
      - 'Sentiment/**'
      - 'data/**'
      - 'requirements-backend.txt'
      - 'Dockerfile'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - uses: google-github-actions/setup-gcloud@v2

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy reva-backend \
            --source . \
            --region asia-southeast1 \
            --platform managed \
            --allow-unauthenticated \
            --memory 4Gi \
            --cpu 2 \
            --min-instances 0 \
            --max-instances 3 \
            --port 8000 \
            --timeout 300 \
            --project ${{ secrets.GCP_PROJECT_ID }} \
            --quiet
```

---

## 📊 Useful Management Commands

```bash
# Stream live logs
gcloud run services logs tail reva-backend --region asia-southeast1

# Update a single environment variable
gcloud run services update reva-backend --region asia-southeast1 --update-env-vars "KEY=VALUE"

# Describe service (shows URL, env vars, traffic split)
gcloud run services describe reva-backend --region asia-southeast1

# List all revisions
gcloud run revisions list --service reva-backend --region asia-southeast1

# Roll back to previous revision
gcloud run services update-traffic reva-backend \
  --region asia-southeast1 \
  --to-revisions PREVIOUS_REVISION_NAME=100
```

---

## 🔥 Troubleshooting

### Container fails to start / OOMKilled

The ML models (TensorFlow, PyTorch, CatBoost) load ~3–4 GB into RAM at startup.

- **Symptom:** Cloud Run shows "Container failed to start" or exits with code 137.
- **Fix:** Ensure `--memory 4Gi` is set. Do **not** reduce below 2Gi.

### Health check failing on startup

The container needs ~60–90 s to load all models before `/health` is ready.

- **Fix:** The `Dockerfile` has `--start-period=90s` — this gives the app 90 s before health check retries begin counting.
- If you're using Cloud Run's startup probe: set **initial delay ≥ 60s**.

### Slow first build

- **Cause:** Cloud Build downloads the full `requirements-backend.txt` (~4–6 GB) from scratch on first build.
- **Fix:** Subsequent builds use Docker layer cache — only changed layers re-download. This is normal.

### CORS errors in the frontend

Ensure `CORS_ORIGINS` includes your Vercel URL (comma-separated, no trailing slash):

```bash
gcloud run services update reva-backend \
  --region asia-southeast1 \
  --update-env-vars "CORS_ORIGINS=https://reva-front.vercel.app,https://your-custom-domain.com"
```

### `gcloud run deploy --source .` uploads too slowly

- **Cause:** Large files in the Docker build context.
- **Fix:** Check `.dockerignore` includes `node_modules`, `frontend/`, `.venv`, `venv`, `data/`, `reports/`.

### Cold start latency

With `--min-instances 0`, the first request after idle will take 45–90 s (model loading).

- **Fix for production:** Set `--min-instances 1` to keep one instance warm (adds ~$15–20/month for 4Gi/2CPU in Singapore).

---

## 📎 Related Docs

- [`docs/gcp-secrets-setup.md`](./gcp-secrets-setup.md) — Store secrets in GCP Secret Manager
- [`scripts/deploy_cloudrun.sh`](../scripts/deploy_cloudrun.sh) — Automated deploy script
