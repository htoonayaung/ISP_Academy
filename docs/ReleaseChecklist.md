# Release Checklist

Use this checklist to freeze the current MVP as `v0.3.0-demo-ready`.

## Pre-Release Verification

```bash
cd /opt/isp-academy
git status
docker compose -f deployments/docker-compose.yml ps
curl http://10.0.44.2:8000/ready
curl -I http://10.0.44.2:3000
```

Expected:

- Git status is clean.
- All platform containers are running.
- Backend readiness is healthy.
- Frontend returns HTTP 200.

## Backup Before Tagging

```bash
cd /opt/isp-academy
bash scripts/backup_database.sh
ls -lh backups/
```

Confirm a new `.dump` file exists.

## Test And Build

```bash
cd /opt/isp-academy
docker compose -f deployments/docker-compose.yml run --rm backend pytest
docker compose -f deployments/docker-compose.yml build frontend
```

## Tag Commands

```bash
cd /opt/isp-academy
git status
bash scripts/backup_database.sh
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
- Backend tests pass.
- Frontend build passes.
- Browser demo flow passes.
- Security boundary remains unchanged.
- Release tag is created locally.
- Tag is pushed only after credentials/SSH are safely configured.
