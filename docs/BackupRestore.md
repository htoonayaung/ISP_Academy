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

## PostgreSQL Restore

Use the helper script with a backup path:

```bash
cd /opt/isp-academy
bash scripts/restore_database.sh backups/isp_academy_YYYYmmdd_HHMMSS.dump
```

Restore replaces database objects in the target database. Confirm you are restoring to the intended environment.

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
git tag phase-7.5-demo-ready
```

Push tags only after reviewing that no secrets are staged or committed.

## Environment Secret Warning

Never commit:

- `deployments/env/backend.env`
- JWT secret values.
- PostgreSQL passwords.
- GitHub tokens.
- Real admin passwords.

Keep only `.env.example` files in Git.
