# Q-Logic Branch Strategy

## Branch Model

We follow a **trunk-based development** model with environment branches:

```
main            ← production (auto-deploys to prod)
  └─ develop    ← integration (auto-deploys to staging)
       └─ feature/*   ← short-lived feature branches
       └─ fix/*       ← bug fix branches
       └─ infra/*     ← infrastructure / terraform changes
```

## Branch Definitions

| Branch | Purpose | Deploys To | Protected | Merge Via |
|--------|---------|------------|-----------|-----------|
| `main` | Production-ready code | **prod** | Yes — requires PR + 1 approval + CI pass | PR from `develop` |
| `develop` | Integration / staging | **staging** | Yes — requires PR + CI pass | PR from feature branches |
| `feature/*` | New functionality | — | No | PR into `develop` |
| `fix/*` | Bug fixes | — | No | PR into `develop` |
| `infra/*` | Terraform / CI / Docker changes | — | No | PR into `develop` |

## Naming Conventions

```
feature/short-description       e.g. feature/queue-priority-rules
fix/issue-number-description    e.g. fix/42-csv-encoding-error
infra/what-changed              e.g. infra/add-cloud-armor-waf
```

- Use lowercase, hyphens only (no underscores or slashes beyond the prefix)
- Keep branch names under 50 characters
- Include ticket/issue numbers when applicable

## Workflow

### Starting New Work

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
```

### During Development

1. Commit frequently with clear messages (see Commit Message Format below)
2. Push your branch regularly: `git push -u origin feature/my-feature`
3. Keep your branch up to date: `git rebase origin/develop`

### Completing Work

1. Run the **Post-Change Checklist** (below)
2. Push final changes
3. Open a PR into `develop`
4. After CI passes and review approval → squash merge into `develop`
5. Delete the feature branch

### Releasing to Production

1. Open a PR from `develop` into `main`
2. PR description must include what's shipping and any migration steps
3. After approval → merge (no squash — preserve history)
4. Tag the merge commit: `git tag -a v1.x.x -m "Release description"`

## Commit Message Format

```
<type>: <short summary>

<optional body — explain WHY, not WHAT>
```

**Types:**
- `feat` — new functionality
- `fix` — bug fix
- `refactor` — code restructuring (no behavior change)
- `infra` — CI/CD, Docker, Terraform, deployment
- `docs` — documentation only
- `test` — adding or updating tests
- `chore` — dependency updates, config tweaks

**Examples:**
```
feat: add priority-based queue ordering
fix: prevent duplicate queue entries on re-enqueue
infra: add Cloud Armor WAF rules to terraform
```

---

## Post-Change Checklist

Run through this checklist after **every code change** before pushing:

### Code Quality
- [ ] Code compiles / imports without errors
- [ ] No hardcoded secrets, passwords, or API keys
- [ ] No `print()` statements — use structured logging (`structlog`)
- [ ] Error handling uses specific exceptions, not bare `except Exception`
- [ ] New environment variables added to `backend/.env.example`

### Database
- [ ] Model changes have a corresponding Alembic migration
- [ ] New foreign keys have indexes (check `__table_args__`)
- [ ] Migration is reversible (`downgrade()` implemented)

### API
- [ ] New endpoints have Pydantic request/response schemas
- [ ] Endpoints that modify data require authentication (`Depends(get_current_user)`)
- [ ] Admin-only endpoints use `Depends(require_role(Role.ADMIN))`
- [ ] Error responses don't leak internal details

### Frontend
- [ ] Components use Angular standalone component pattern
- [ ] API calls go through `ApiService` (not direct `HttpClient`)
- [ ] Loading and error states are handled in the UI

### Infrastructure
- [ ] Docker builds successfully: `docker compose build`
- [ ] Terraform changes validated: `terraform validate` and `terraform plan`
- [ ] CI workflow updated if new test/build steps are needed

### Testing
- [ ] New features have unit tests
- [ ] Existing tests still pass
- [ ] Edge cases covered (empty inputs, large payloads, concurrent access)

### Git Hygiene
- [ ] Branch is up to date with `develop`: `git rebase origin/develop`
- [ ] Commits follow the message format above
- [ ] No unrelated changes bundled into the commit
- [ ] Sensitive files excluded (`.env`, `.tfvars`, credentials)

---

## Hotfix Process

For critical production bugs that can't wait for the normal flow:

```bash
git checkout main
git pull origin main
git checkout -b fix/critical-issue-description
# ... fix the issue ...
# Open PR directly into main (skip develop)
# After merge to main, immediately cherry-pick into develop:
git checkout develop
git cherry-pick <commit-hash>
git push origin develop
```

## Environment Mapping

| Branch | Environment | URL Pattern | Database |
|--------|-------------|-------------|----------|
| `main` | Production | `qlogic.example.com` | Cloud SQL (HA) |
| `develop` | Staging | `staging.qlogic.example.com` | Cloud SQL (single) |
| Feature branches | Local only | `localhost:4200` | Docker PostgreSQL |
