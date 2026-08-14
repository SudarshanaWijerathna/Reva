#!/usr/bin/env bash
# =============================================================================
# deploy_cloudrun.sh — Deploy Reva backend to Google Cloud Run
# =============================================================================
# Usage:
#   chmod +x scripts/deploy_cloudrun.sh
#   ./scripts/deploy_cloudrun.sh
#
# Optionally, pre-fill secrets to avoid interactive prompts:
#   cp .env.example .env.cloudrun   # fill in real values, do NOT commit!
#   ./scripts/deploy_cloudrun.sh
# =============================================================================

set -euo pipefail

# ── Config (edit these if needed) ────────────────────────────────────────────
SERVICE_NAME="reva-backend"
REGION="asia-southeast1"          # Singapore — change to us-central1 if preferred
MEMORY="4Gi"
CPU="2"
MIN_INSTANCES="0"
MAX_INSTANCES="3"
PORT="8000"
FRONTEND_URL="https://reva-front.vercel.app"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        Reva Backend — Google Cloud Run Deploy        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Prerequisites ─────────────────────────────────────────────────────
info "Checking prerequisites..."

if ! command -v gcloud &>/dev/null; then
  error "gcloud CLI not found. Install it from https://cloud.google.com/sdk/docs/install or use Google Cloud Shell."
fi
success "gcloud CLI found: $(gcloud --version | head -1)"

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
if [[ -z "$PROJECT_ID" ]]; then
  error "No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
fi
success "GCP Project: ${PROJECT_ID}"

ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -1)
if [[ -z "$ACCOUNT" ]]; then
  error "Not authenticated. Run: gcloud auth login"
fi
success "Authenticated as: ${ACCOUNT}"

# ── Step 2: Enable required APIs ──────────────────────────────────────────────
info "Enabling required GCP APIs (this may take ~1 min on first run)..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --quiet
success "APIs enabled."

# ── Step 3: Load secrets ──────────────────────────────────────────────────────
ENV_FILE=".env.cloudrun"

if [[ -f "$ENV_FILE" ]]; then
  info "Loading secrets from ${ENV_FILE} ..."
  # shellcheck disable=SC2046
  set -o allexport
  # Read non-comment, non-empty lines
  while IFS= read -r line; do
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    export "$line"
  done < "$ENV_FILE"
  set +o allexport
  success "Secrets loaded from ${ENV_FILE}."
else
  warn "No ${ENV_FILE} found. You will be prompted for secrets after deploy."
fi

# ── Step 4: Deploy via Cloud Build ────────────────────────────────────────────
echo ""
info "Deploying '${SERVICE_NAME}' to Cloud Run in ${REGION}..."
info "⏳  Cloud Build will build the Docker image — first run takes ~15–25 min (heavy ML deps)."
echo ""

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --memory "${MEMORY}" \
  --cpu "${CPU}" \
  --min-instances "${MIN_INSTANCES}" \
  --max-instances "${MAX_INSTANCES}" \
  --port "${PORT}" \
  --timeout 300 \
  --concurrency 10 \
  --set-env-vars "ENABLE_SCHEDULER=false,MODEL_RUNTIME_MODE=embedded,PORTFOLIO_VALUATION_ENGINE=legacy,CORS_ORIGINS=${FRONTEND_URL}" \
  --quiet

# ── Step 5: Retrieve service URL ──────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format "value(status.url)")

success "Service deployed at: ${SERVICE_URL}"

# ── Step 6: Set secret environment variables ──────────────────────────────────
echo ""
info "Setting secret environment variables..."

prompt_if_empty() {
  local var_name="$1"
  local prompt_text="$2"
  local current_val="${!var_name:-}"
  if [[ -z "$current_val" ]]; then
    read -r -p "  Enter ${prompt_text}: " current_val
  fi
  echo "$current_val"
}

DATABASE_URL=$(prompt_if_empty DATABASE_URL "DATABASE_URL (PostgreSQL connection string)")
SECRET_KEY=$(prompt_if_empty SECRET_KEY "SECRET_KEY (JWT signing secret)")
GEMINI_API_KEY=$(prompt_if_empty GEMINI_API_KEY "GEMINI_API_KEY")
NEWS_API=$(prompt_if_empty NEWS_API "NEWS_API key (press Enter to skip)")
DB_LINK=$(prompt_if_empty DB_LINK "DB_LINK (MongoDB URL, press Enter to skip)")
REDIS_URL=$(prompt_if_empty REDIS_URL "REDIS_URL (press Enter to skip)")

ENV_VARS="DATABASE_URL=${DATABASE_URL},SECRET_KEY=${SECRET_KEY},GEMINI_API_KEY=${GEMINI_API_KEY}"
[[ -n "$NEWS_API" ]]   && ENV_VARS="${ENV_VARS},NEWS_API=${NEWS_API}"
[[ -n "$DB_LINK" ]]    && ENV_VARS="${ENV_VARS},DB_LINK=${DB_LINK}"
[[ -n "$REDIS_URL" ]]  && ENV_VARS="${ENV_VARS},REDIS_URL=${REDIS_URL}"

gcloud run services update "${SERVICE_NAME}" \
  --region "${REGION}" \
  --update-env-vars "${ENV_VARS}" \
  --quiet

success "Secrets applied."

# ── Step 7: Health check ──────────────────────────────────────────────────────
echo ""
info "Running health check..."
sleep 5   # brief pause for the new revision to roll out

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/health" || true)
if [[ "$HTTP_CODE" == "200" ]]; then
  success "Health check passed! (/health returned 200)"
else
  warn "Health check returned HTTP ${HTTP_CODE}. The service may still be starting — try again in 60s."
  warn "Check logs: gcloud run services logs tail ${SERVICE_NAME} --region ${REGION}"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  Reva Backend is live!                           ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  URL:    ${SERVICE_URL}${NC}"
echo -e "${GREEN}║  Health: ${SERVICE_URL}/health${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Next step — update Vercel frontend:                 ║${NC}"
echo -e "${GREEN}║  Set VITE_API_BASE_URL = ${SERVICE_URL}${NC}"
echo -e "${GREEN}║  in Vercel → reva-front → Settings → Env Vars       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
