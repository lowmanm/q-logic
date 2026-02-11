# GCP Setup Guide — Q-Logic

This is a sequential, copy-paste guide. Do every step in order.
Replace `YOUR_PROJECT_ID` with your actual GCP project ID throughout.

---

## Prerequisites

- [ ] Google Cloud SDK (`gcloud`) installed locally
- [ ] Terraform >= 1.5.0 installed locally
- [ ] A GCP billing account
- [ ] Owner access to the GCP project (or permissions to create one)
- [ ] Your GitHub repo URL (e.g. `github.com/lowmanm/q-logic`)

---

## Phase 1: GCP Project Foundation

### 1.1 — Create or select a project

```bash
# Option A: Create a new project
gcloud projects create YOUR_PROJECT_ID --name="Q-Logic"

# Option B: Use an existing project
gcloud config set project YOUR_PROJECT_ID
```

### 1.2 — Link billing

```bash
# List your billing accounts
gcloud billing accounts list

# Link billing to the project
gcloud billing projects link YOUR_PROJECT_ID \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

### 1.3 — Enable all required APIs

```bash
gcloud services enable \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  servicenetworking.googleapis.com \
  run.googleapis.com \
  vpcaccess.googleapis.com \
  sts.googleapis.com
```

> `sts.googleapis.com` and `iamcredentials.googleapis.com` are specifically
> needed for Workload Identity Federation (GitHub Actions auth).

---

## Phase 2: Terraform State Bucket

Terraform needs a GCS bucket to store its state file before it can create anything.

```bash
# Create the bucket (pick your region)
gcloud storage buckets create gs://YOUR_PROJECT_ID-terraform-state \
  --location=us-central1 \
  --uniform-bucket-level-access

# Enable versioning (so you can recover from bad state)
gcloud storage buckets update gs://YOUR_PROJECT_ID-terraform-state \
  --versioning
```

---

## Phase 3: Service Accounts

You need two service accounts with different scopes:

### 3.1 — Terraform service account (infra provisioning)

```bash
gcloud iam service-accounts create terraform \
  --display-name="Terraform Admin"

# Grant roles
for ROLE in \
  roles/editor \
  roles/iam.securityAdmin \
  roles/secretmanager.admin \
  roles/cloudsql.admin \
  roles/artifactregistry.admin \
  roles/compute.networkAdmin \
  roles/servicenetworking.networksAdmin \
  roles/vpcaccess.admin; do
  gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:terraform@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="$ROLE"
done
```

### 3.2 — Cloud Run service account (application runtime)

```bash
gcloud iam service-accounts create qlogic-app \
  --display-name="Q-Logic App Runtime"

# Grant roles (minimal — only what the app needs at runtime)
for ROLE in \
  roles/secretmanager.secretAccessor \
  roles/cloudsql.client \
  roles/logging.logWriter \
  roles/monitoring.metricWriter; do
  gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:qlogic-app@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="$ROLE"
done
```

---

## Phase 4: Workload Identity Federation (GitHub Actions → GCP)

This is how GitHub Actions authenticates to GCP **without a JSON key file**.
It's the recommended approach — no secrets to rotate or leak.

### 4.1 — Create a Workload Identity Pool

```bash
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

### 4.2 — Create a Provider in the pool (linked to your GitHub repo)

```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='lowmanm/q-logic'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

> **IMPORTANT**: Change `lowmanm/q-logic` to your actual GitHub `org/repo`.
> The `attribute-condition` ensures only YOUR repo can assume this identity.

### 4.3 — Get the full provider resource name

```bash
gcloud iam workload-identity-pools providers describe "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

This outputs something like:
```
projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

**Save this value** — it becomes the `WIF_PROVIDER` secret in GitHub.

### 4.4 — Allow GitHub Actions to impersonate the Terraform SA

```bash
gcloud iam service-accounts add-iam-policy-binding \
  terraform@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/lowmanm/q-logic"
```

> This says: "GitHub Actions running from the `lowmanm/q-logic` repo can
> act as the `terraform` service account."

### 4.5 — Also allow it to impersonate the app SA (for Cloud Run deploys)

```bash
gcloud iam service-accounts add-iam-policy-binding \
  qlogic-app@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/lowmanm/q-logic"
```

### 4.6 — Grant the terraform SA permission to deploy to Cloud Run and push images

```bash
for ROLE in \
  roles/run.admin \
  roles/artifactregistry.writer \
  roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:terraform@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="$ROLE"
done
```

---

## Phase 5: Configure GitHub Repository

### 5.1 — Set GitHub Secrets

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**.

Create these **Secrets**:

| Secret Name | Value |
|---|---|
| `WIF_PROVIDER` | The full provider name from step 4.3 (e.g. `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider`) |
| `WIF_SERVICE_ACCOUNT` | `terraform@YOUR_PROJECT_ID.iam.gserviceaccount.com` |

### 5.2 — Set GitHub Variables

Go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab.

Create this **Variable** (not a secret — it's not sensitive):

| Variable Name | Value |
|---|---|
| `GCP_PROJECT_ID` | `YOUR_PROJECT_ID` |

### 5.3 — Verify the CI workflow references

The CI workflow (`.github/workflows/ci.yml`) already references these correctly:
- `${{ secrets.WIF_PROVIDER }}` — for the provider
- `${{ secrets.WIF_SERVICE_ACCOUNT }}` — for the service account
- `${{ vars.GCP_PROJECT_ID }}` — for the project ID

---

## Phase 6: Create Secrets in Secret Manager

```bash
# Database password
echo -n "$(openssl rand -base64 32)" | \
  gcloud secrets create db-password --data-file=- --project=YOUR_PROJECT_ID

# JWT secret
echo -n "$(openssl rand -base64 64)" | \
  gcloud secrets create jwt-secret --data-file=- --project=YOUR_PROJECT_ID

# CORS origins (update with your actual domain later)
echo -n '["https://qlogic.yourorg.com"]' | \
  gcloud secrets create cors-origins --data-file=- --project=YOUR_PROJECT_ID
```

To retrieve the db-password later (you'll need it for the Terraform tfvars):
```bash
gcloud secrets versions access latest --secret=db-password --project=YOUR_PROJECT_ID
```

---

## Phase 7: Run Terraform (Provision Infrastructure)

### 7.1 — Authenticate locally for Terraform

```bash
# Option A: Use your personal credentials (simplest for first-time setup)
gcloud auth application-default login

# Option B: Use the terraform service account key (if you created one)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/tf-key.json
```

### 7.2 — Create tfvars for dev environment

```bash
cat > infra/environments/dev/terraform.tfvars <<'EOF'
project_id         = "YOUR_PROJECT_ID"
region             = "us-central1"
db_password        = "PASTE_FROM_SECRET_MANAGER"
cloud_run_sa_email = "qlogic-app@YOUR_PROJECT_ID.iam.gserviceaccount.com"
EOF
```

> **Never commit this file.** It's already in `.gitignore`.

### 7.3 — Initialize and apply

```bash
cd infra/environments/dev

# Init with the state bucket
terraform init \
  -backend-config="bucket=YOUR_PROJECT_ID-terraform-state"

# Preview what will be created
terraform plan

# Apply (creates VPC, Cloud SQL, Artifact Registry, Cloud Run services)
terraform apply
```

This will take 10-15 minutes (Cloud SQL is slow to provision).

### 7.4 — Note the outputs

```bash
terraform output
```

You'll get:
- `backend_url` — your Cloud Run backend URL
- `frontend_url` — your Cloud Run frontend URL
- `db_connection_name` — needed for Cloud SQL Auth Proxy
- `db_private_ip` — the internal IP of your database

---

## Phase 8: First Deployment

After Terraform creates the infrastructure, you need to push your first Docker images.

### 8.1 — Build and push images locally (one-time bootstrap)

```bash
# Authenticate Docker to Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

REPO="us-central1-docker.pkg.dev/YOUR_PROJECT_ID/qlogic"

# Build and push backend
docker build --target production -t $REPO/backend:latest ./backend
docker push $REPO/backend:latest

# Build and push frontend
docker build -t $REPO/frontend:latest ./frontend
docker push $REPO/frontend:latest
```

### 8.2 — Run database migrations

```bash
# Use Cloud SQL Auth Proxy locally to connect to the remote DB
cloud-sql-proxy YOUR_PROJECT_ID:us-central1:qlogic-dev-db &

# Then run migrations
cd backend
DB_HOST=127.0.0.1 DB_PORT=5432 DB_NAME=qlogic \
  DB_USER=qlogic_app DB_PASSWORD="PASTE_PASSWORD" \
  alembic upgrade head

# Seed the admin user
curl -X POST https://YOUR_BACKEND_URL/api/auth/seed-admin
```

### 8.3 — Redeploy Cloud Run to pick up the images

```bash
# Backend
gcloud run services update qlogic-dev-backend \
  --image=$REPO/backend:latest \
  --region=us-central1

# Frontend
gcloud run services update qlogic-dev-frontend \
  --image=$REPO/frontend:latest \
  --region=us-central1
```

After this, every push to `develop` or `main` will auto-deploy via GitHub Actions.

---

## Verification Checklist

After everything is up:

- [ ] `curl https://YOUR_BACKEND_URL/api/health` returns `{"status":"ok"}`
- [ ] `curl https://YOUR_BACKEND_URL/api/health/ready` returns `{"status":"ready","database":"connected"}`
- [ ] You can hit `POST /api/auth/seed-admin` and get an admin user back
- [ ] You can login with `admin@qlogic.local` / `admin` and get a JWT
- [ ] Frontend loads at the frontend URL and shows the login page
- [ ] GitHub Actions CI passes on a push to `develop`

---

## Cost Estimates (Dev Environment)

| Resource | Tier | Estimated Monthly |
|---|---|---|
| Cloud SQL | db-f1-micro | ~$10 |
| Cloud Run (backend) | 0-2 instances | ~$5-15 |
| Cloud Run (frontend) | 0-2 instances | ~$2-5 |
| Artifact Registry | Storage only | ~$1 |
| VPC Connector | Minimum 2 instances | ~$15 |
| Secret Manager | 4 secrets | < $1 |
| **Total** | | **~$35-50/mo** |

For production (HA Cloud SQL, min instances=1), expect ~$150-200/mo.
