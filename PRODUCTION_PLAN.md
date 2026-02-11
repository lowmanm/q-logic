# Q-Logic Production Deployment Plan

## Plan File
This document contains the implementation plan for production-readying the Q-Logic codebase
and the GCP resource checklist the operator must complete.

---

## PART 1: GCP Resource Checklist (Manual / Console + Terraform)

### Step 1 — GCP Project & IAM Foundation
- [ ] Create a GCP project (e.g. `qlogic-prod`) or select existing
- [ ] Enable billing on the project
- [ ] Enable required APIs:
  ```
  gcloud services enable \
    compute.googleapis.com \
    container.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    servicenetworking.googleapis.com \
    run.googleapis.com
  ```
- [ ] Create a Terraform service account:
  ```
  gcloud iam service-accounts create terraform \
    --display-name="Terraform Admin"
  ```
- [ ] Grant roles to the Terraform SA:
  - `roles/editor`
  - `roles/secretmanager.admin`
  - `roles/iam.securityAdmin`
  - `roles/cloudsql.admin`
  - `roles/artifactregistry.admin`
- [ ] Create and download a key (or use Workload Identity Federation for CI):
  ```
  gcloud iam service-accounts keys create tf-key.json \
    --iam-account=terraform@<PROJECT_ID>.iam.gserviceaccount.com
  ```
- [ ] Store `tf-key.json` securely (never commit to git)

### Step 2 — Networking
- [ ] Decide on region (e.g. `us-central1`)
- [ ] Create a VPC with private subnets (Terraform will handle this)
- [ ] Allocate a private IP range for VPC peering (Cloud SQL)
- [ ] Enable Private Services Access for Cloud SQL connectivity

### Step 3 — Cloud SQL (PostgreSQL)
- [ ] Choose instance tier:
  - Dev/staging: `db-f1-micro` or `db-g1-small`
  - Production: `db-custom-2-7680` (2 vCPU, 7.5 GB) minimum
- [ ] Decide on High Availability (regional) vs single-zone
- [ ] Enable automated backups with point-in-time recovery
- [ ] Set maintenance window (e.g. Sunday 03:00 UTC)
- [ ] Generate a strong database password, store in Secret Manager:
  ```
  echo -n "$(openssl rand -base64 32)" | \
    gcloud secrets create db-password --data-file=-
  ```
- [ ] Create the `qlogic` database and `qlogic_app` user (not `postgres`)

### Step 4 — Artifact Registry
- [ ] Create a Docker repository:
  ```
  gcloud artifacts repositories create qlogic \
    --repository-format=docker \
    --location=us-central1
  ```
- [ ] Configure Docker auth:
  ```
  gcloud auth configure-docker us-central1-docker.pkg.dev
  ```

### Step 5 — Secret Manager
- [ ] Create the following secrets:
  | Secret Name           | Value                                      |
  |-----------------------|--------------------------------------------|
  | `db-password`         | PostgreSQL password for `qlogic_app` user  |
  | `db-host`             | Cloud SQL private IP (or connection name)   |
  | `jwt-secret`          | `openssl rand -base64 64`                  |
  | `cors-origins`        | `https://qlogic.yourorg.com`               |

### Step 6 — Compute (Choose One)
**Option A: Cloud Run (recommended for starting)**
- [ ] No cluster to manage
- [ ] Set min instances = 1 (avoid cold starts), max = 10
- [ ] Connect to Cloud SQL via VPC connector
- [ ] Create a Serverless VPC Access connector:
  ```
  gcloud compute networks vpc-access connectors create qlogic-connector \
    --region=us-central1 \
    --subnet=<SUBNET_NAME>
  ```

**Option B: GKE Autopilot (recommended for scale)**
- [ ] Create GKE Autopilot cluster in the VPC
- [ ] Install Cloud SQL Auth Proxy as a sidecar or use Workload Identity
- [ ] Set up namespaces: `qlogic-dev`, `qlogic-staging`, `qlogic-prod`

### Step 7 — DNS & SSL
- [ ] Register or delegate a domain (e.g. `qlogic.yourorg.com`)
- [ ] Create a Cloud Load Balancer (HTTPS) or use Cloud Run's built-in
- [ ] Provision a managed SSL certificate:
  ```
  gcloud compute ssl-certificates create qlogic-cert \
    --domains=qlogic.yourorg.com
  ```

### Step 8 — Monitoring & Logging
- [ ] Cloud Logging is automatic for Cloud Run / GKE
- [ ] Create an uptime check for `/api/health`
- [ ] Create alert policies:
  - 5xx rate > 1% over 5 min
  - Latency p99 > 5s
  - Cloud SQL CPU > 80%
  - Cloud SQL connections > 80% of max
- [ ] Set up a notification channel (email, Slack, PagerDuty)

### Step 9 — CI/CD
- [ ] Create a Cloud Build trigger connected to your GitHub repo
  - OR use GitHub Actions with Workload Identity Federation
- [ ] Set up branch-based deployment:
  - `main` → production
  - `develop` → staging
- [ ] Store `tf-key.json` as a GitHub secret (if using GH Actions)

### Step 10 — Terraform State
- [ ] Create a GCS bucket for Terraform remote state:
  ```
  gsutil mb -l us-central1 gs://<PROJECT_ID>-terraform-state
  gsutil versioning set on gs://<PROJECT_ID>-terraform-state
  ```

---

## PART 2: Codebase Production-Readiness Plan

### Phase A — Configuration & Secrets (P0)
1. Decompose DATABASE_URL into individual env vars (host, port, name, user, password)
2. Build DATABASE_URL dynamically in config.py from components
3. Add all missing env vars to Settings (LOG_LEVEL, ENVIRONMENT, JWT_SECRET, BATCH_SIZE, etc.)
4. Create `.env.example` with every variable documented
5. Remove all hardcoded credentials from docker-compose.yml, alembic.ini
6. Add database connection pool tuning (pool_size, max_overflow, pool_pre_ping, pool_recycle)
7. Add SSL mode support for Cloud SQL connections

### Phase B — Structured Logging & Error Handling (P0)
1. Add Python `structlog` with JSON output
2. Add request_id middleware (generate UUID per request, attach to all logs)
3. Add request/response logging middleware (method, path, status, duration)
4. Replace bare `except Exception` with structured error responses
5. Never expose internal error details to client in non-dev environments
6. Add correlation ID header propagation

### Phase C — Authentication & Authorization (P0)
1. Add Google Identity Platform / Firebase Auth as the identity provider
2. Add JWT validation middleware — decode and verify on every request
3. Add role-based access: `admin`, `supervisor`, `agent`
4. Protect endpoints by role:
   - Schema/provisioning: `admin` only
   - Queue management: `admin`, `supervisor`
   - Agent workspace (next/complete/skip): `agent`, `supervisor`
   - Metrics: `supervisor`, `admin`
   - Employee CRUD: `admin`
5. Add `current_user` dependency injection from JWT claims

### Phase D — Database Hardening (P0)
1. Generate initial Alembic migration from current models
2. Remove `Base.metadata.create_all()` from lifespan
3. Add migration run to deployment pipeline (pre-deploy step)
4. Add indexes on all foreign keys and heavily-queried columns
5. Add `sslmode=require` to connection strings for production

### Phase E — Docker & Deployment (P1)
1. Multi-stage backend Dockerfile: builder → production (no dev deps, no --reload)
2. Add non-root USER directive
3. Add HEALTHCHECK to both Dockerfiles
4. Add resource limits to docker-compose
5. Remove exposed database port from docker-compose
6. Add restart policies
7. Frontend nginx: add security headers, gzip, caching

### Phase F — CI/CD Pipeline (P1)
1. GitHub Actions workflow: lint → test → build → push images → deploy
2. Separate jobs for backend and frontend
3. Terraform plan/apply step for infra changes
4. Database migration step in deploy pipeline

### Phase G — IaC Repository Structure (Terraform)
```
infra/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   └── ...
│   └── prod/
│       └── ...
├── modules/
│   ├── networking/       # VPC, subnets, firewall rules
│   ├── database/         # Cloud SQL instance, users, databases
│   ├── secrets/          # Secret Manager secrets
│   ├── registry/         # Artifact Registry
│   ├── compute/          # Cloud Run services or GKE
│   └── monitoring/       # Uptime checks, alerts
├── backend.tf            # GCS remote state config
└── versions.tf           # Provider version constraints
```

### Phase H — Observability (P1)
1. Add `/api/health` deep check (verify DB connectivity)
2. Add `/api/health/ready` readiness probe
3. Add OpenTelemetry instrumentation for request tracing
4. Export metrics to Cloud Monitoring

---

## Execution Order

```
Phase A (Config & Secrets)      ← do first, everything depends on this
    ↓
Phase B (Logging)               ← enables debugging everything after
    ↓
Phase D (Database Hardening)    ← migrations before auth schema changes
    ↓
Phase C (Auth)                  ← needs logging, needs clean DB strategy
    ↓
Phase E (Docker Hardening)      ← package everything properly
    ↓
Phase F (CI/CD) + Phase G (IaC) ← run in parallel
    ↓
Phase H (Observability)         ← final layer
```
