# Release Checklist

Use this checklist to freeze the current MVP as `v0.3.0-demo-ready`.

## Pre-Release Verification

```bash
cd /opt/isp-academy
git status
docker compose -f deployments/docker-compose.yml ps
curl http://10.0.44.2:8000/ready
curl -I http://10.0.44.2:3000
bash scripts/check_system_health.sh
bash scripts/security_smoke_check.sh
bash scripts/check_lab_runtime_state.sh
```

Expected:

- Git status is clean.
- All platform containers are running.
- Backend readiness is healthy.
- Frontend returns HTTP 200.
- Security smoke check does not show critical backend/frontend container boundary failures.

## Backup Before Tagging

```bash
cd /opt/isp-academy
bash scripts/backup_database.sh
ls -lh backups/
```

Confirm a new `.dump` file exists.

Verify it:

```bash
latest="$(ls -t backups/*.dump | head -n 1)"
bash scripts/verify_backup_file.sh "$latest"
```

## Test And Build

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml run --rm backend pytest
docker compose -f deployments/docker-compose.yml build frontend
```

## Phase 10 Operations Checks

```bash
cd /opt/isp-academy
bash scripts/check_system_health.sh
bash scripts/security_smoke_check.sh
bash scripts/check_lab_runtime_state.sh
docker system df
```

## Tag Commands

```bash
cd /opt/isp-academy
git status
bash scripts/security_smoke_check.sh
bash scripts/backup_database.sh
latest="$(ls -t backups/*.dump | head -n 1)"
bash scripts/verify_backup_file.sh "$latest"
git tag -a v0.3.0-demo-ready -m "Demo-ready MVP release"
git push
git push origin v0.3.0-demo-ready
```

## If Git Push Over HTTPS Fails

Use an SSH remote instead of pasting tokens into shell prompts, docs, screenshots, or chat.

Example:

```bash
cd /opt/isp-academy
git remote set-url origin git@github.com:htoonayaung/ISP_Academy.git
git push
git push origin v0.3.0-demo-ready
```

Only use this after SSH keys are configured on the server and GitHub.

## Never Commit Or Share

- `deployments/env/backend.env`
- API keys
- GitHub tokens
- JWT secrets
- PostgreSQL passwords
- Admin passwords
- Demo passwords
- Backup dumps
- Backup SQL files

## Final Browser Rehearsal

1. Admin opens Demo Setup.
2. Confirm `Demo Ready`.
3. Student opens recommended demo ticket.
4. Student starts attempt.
5. Student starts lab.
6. Lab reaches `RUNNING`.
7. Student runs verification.
8. Result shows `PASSED`.
9. Student destroys lab.
10. Confirm no demo lab containers remain.

## Release Is Ready When

- Git status is clean.
- Backup exists.
- Backup file has been verified and copied off the server when needed.
- Backend tests pass.
- Frontend build passes.
- Health check script passes.
- Security smoke check passes or has only acknowledged worker privilege warning.
- Lab runtime state check has no unexpected running labs.
- Browser demo flow passes.
- Security boundary remains unchanged.
- Demo passwords have been rotated if needed.
- No secrets are staged or committed.
- Release tag is created locally.
- Tag is pushed only after credentials/SSH are safely configured.
