# GCP Secret Manager — Reva Backend Secrets Guide

Store your API keys and database credentials in **Google Cloud Secret Manager** instead of plaintext Cloud Run environment variables. This prevents secrets from appearing in Cloud Run revision history, `gcloud` command logs, or CI/CD artifacts.

---

## Why Secret Manager?

| Approach | Secrets in revision history? | Requires IAM? | Recommended? |
|---|---|---|---|
| `--set-env-vars` | ✅ Yes (visible in console) | No | ❌ Dev/testing only |
| `--set-secrets` (Secret Manager) | ❌ No | Yes (simple) | ✅ Production |

---

## Step 1 — Create Secrets

Run these in **Cloud Shell** or your local terminal (replace placeholder values):

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION="asia-southeast1"

# Create each secret
echo -n "postgresql+psycopg2://user:pass@host:5432/reva?sslmode=require" \
  | gcloud secrets create DATABASE_URL --data-file=- --replication-policy=automatic

echo -n "your-super-secret-jwt-key-here" \
  | gcloud secrets create SECRET_KEY --data-file=- --replication-policy=automatic

echo -n "your-gemini-api-key" \
  | gcloud secrets create GEMINI_API_KEY --data-file=- --replication-policy=automatic

# Optional secrets
echo -n "your-news-api-key" \
  | gcloud secrets create NEWS_API --data-file=- --replication-policy=automatic

echo -n "mongodb+srv://user:pass@cluster.mongodb.net/db" \
  | gcloud secrets create DB_LINK --data-file=- --replication-policy=automatic

echo -n "rediss://username:password@host:port" \
  | gcloud secrets create REDIS_URL --data-file=- --replication-policy=automatic
```

To **update** an existing secret value:
```bash
echo -n "new-value" | gcloud secrets versions add DATABASE_URL --data-file=-
```

---

## Step 2 — Grant Cloud Run Access to the Secrets

Cloud Run uses a **Service Account** to access secrets. You need to grant it the `Secret Manager Secret Accessor` role.

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant access for each secret
for SECRET in DATABASE_URL SECRET_KEY GEMINI_API_KEY NEWS_API DB_LINK REDIS_URL; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet
done

echo "✅ IAM bindings set."
```

---

## Step 3 — Deploy Using `--set-secrets`

When deploying (or updating), reference secrets instead of raw values:

```bash
gcloud run services update reva-backend \
  --region asia-southeast1 \
  --set-secrets "\
DATABASE_URL=DATABASE_URL:latest,\
SECRET_KEY=SECRET_KEY:latest,\
GEMINI_API_KEY=GEMINI_API_KEY:latest,\
NEWS_API=NEWS_API:latest,\
DB_LINK=DB_LINK:latest,\
REDIS_URL=REDIS_URL:latest"
```

The format is `ENV_VAR_NAME=SECRET_NAME:VERSION`. Using `latest` always picks the newest version.

---

## Step 4 — Remove Plaintext Env Vars (if previously set)

If you previously used `--set-env-vars` with secrets, clean them up:

```bash
gcloud run services update reva-backend \
  --region asia-southeast1 \
  --remove-env-vars "DATABASE_URL,SECRET_KEY,GEMINI_API_KEY,NEWS_API,DB_LINK,REDIS_URL"
```

---

## Verify

```bash
# List secret versions
gcloud secrets versions list DATABASE_URL

# Describe the Cloud Run service to confirm --set-secrets are configured
gcloud run services describe reva-backend --region asia-southeast1 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

---

## Rotating a Secret

```bash
# Add a new version
echo -n "new-password-here" | gcloud secrets versions add DATABASE_URL --data-file=-

# Cloud Run automatically picks up :latest on the next request (no redeploy needed!)
```

---

## Resources

- [Secret Manager Docs](https://cloud.google.com/secret-manager/docs)
- [Using Secrets in Cloud Run](https://cloud.google.com/run/docs/configuring/secrets)
- [Cloud Run Service Account](https://cloud.google.com/run/docs/securing/service-identity)
