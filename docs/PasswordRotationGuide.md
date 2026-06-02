# Password And Secret Rotation Guide

## Rules

- Never paste secrets into chat, docs, screenshots, or Git.
- Rotate secrets only on the server or in a trusted password manager.
- Review `git status --short` before every commit.
- Keep `deployments/env/backend.env` out of Git.

## Admin Password Rotation

Phase 9C added Admin reset password support.

From the UI:

1. Log in as Admin.
2. Open `Users`.
3. Click `Reset Password` for the target user.
4. Enter a new strong password.
5. Share it through a secure channel only.

API endpoint:

```text
POST /api/v1/users/{user_id}/reset-password
```

Do not include real passwords in examples, logs, or docs.

## Demo Password Rotation

Demo credentials are internal-demo only.

Options:

- Use Admin `Users` page to reset `demo_instructor` and `demo_student`.
- Or run Demo Reset and Demo Setup again if you intentionally want a fresh demo set.

If demo passwords are stored in `deployments/env/backend.env`, update them there and restart backend before running setup.

## JWT Secret Rotation

`JWT_SECRET_KEY` must come from environment:

```text
deployments/env/backend.env
```

Rotating it invalidates existing access tokens. Plan a maintenance window:

1. Generate a new long random value.
2. Update `JWT_SECRET_KEY` in `deployments/env/backend.env`.
3. Restart backend.
4. Ask users to log in again.

Never commit the value.

## AI API Key Rotation

AI keys are backend-only:

1. Rotate/revoke the key at the provider.
2. Update `AI_API_KEY` in `deployments/env/backend.env`.
3. Restart backend.
4. Confirm Provider Status shows `API Key SET` without revealing the value.

Do not put AI keys in frontend files.

## GitHub Token Rotation

If a GitHub token was exposed:

1. Revoke it immediately in GitHub.
2. Create a new token only if needed.
3. Prefer SSH remotes over HTTPS token prompts.
4. Never paste GitHub tokens into shell history, chat, docs, or screenshots.

## Current MVP Limitation

There is no self-service password change screen yet. Admin reset is the supported MVP path.
