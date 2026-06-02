# Backup And Restore

## What To Back Up

Back up these items before demos, upgrades, and risky maintenance:

- PostgreSQL database.
- `/opt/isp-academy/deployments/env/backend.env`.
- `/opt/isp-academy/lab-storage` when running labs or lab artifacts matter.
- Git repository state and current commit/tag.

Do not commit real secrets or real environment files to Git.

## PostgreSQL Backup

Use the helper script:

```bash
cd /opt/isp-academy
bash scripts/backup_database.sh
```

The script writes a timestamped custom-format dump to:

```text
/opt/isp-academy/backups/
```

Manual equivalent:

```bash
cd /opt/isp-academy/deployments
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > ../backups/isp_academy_YYYYmmdd_HHMMSS.dump
```

## Pre-Release Backup Checklist

Before creating a release tag or running a public demo:

```bash
cd /opt/isp-academy
bash scripts/backup_database.sh
ls -lh backups/
```

Confirm:

- A new `backups/*.dump` file exists.
- The file timestamp matches the current release rehearsal.
- The file size is greater than zero.
- The backup is copied to a safe location outside the server if this is an important demo.

Recommended safe storage:

- Encrypted external drive.
- Private backup server.
- Private cloud storage controlled by the project owner.

Do not store release backups only in the Git repository working tree.

## PostgreSQL Restore

Use the helper script with a backup path:

```bash
cd /opt/isp-academy
bash scripts/restore_database.sh backups/isp_academy_YYYYmmdd_HHMMSS.dump
```

Restore replaces database objects in the target database. Confirm you are restoring to the intended environment.

Restore dry-run warning:

- There is no automatic dry-run restore in the MVP scripts.
- Test restore only on a separate staging server or disposable database.
- Do not test restore against the live demo database unless you intend to replace current data.

Manual equivalent:

```bash
cd /opt/isp-academy/deployments
cat ../backups/isp_academy_YYYYmmdd_HHMMSS.dump | docker compose exec -T postgres sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## LAB_ROOT Backup Note

The MVP lab runtime stores generated lab files under `/opt/isp-academy/lab-storage`.

Example backup:

```bash
sudo tar -czf /opt/isp-academy/backups/lab-storage_$(date +%Y%m%d_%H%M%S).tar.gz -C /opt/isp-academy lab-storage
```

Only restore lab storage when no labs are running.

## Git Tag Recommendation

After a successful demo-readiness check:

```bash
cd /opt/isp-academy
git tag -a v0.3.0-demo-ready -m "Demo-ready MVP release"
```

Push tags only after reviewing that no secrets are staged or committed.

## Environment Secret Warning

Never commit:

- `deployments/env/backend.env`
- API keys.
- JWT secret values.
- PostgreSQL passwords.
- GitHub tokens.
- Real admin passwords.
- Demo passwords.
- `backups/*.dump`
- `backups/*.sql`

Keep only `.env.example` files in Git.
