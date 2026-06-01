# AI Lab Builder Guide

## Purpose

AI Lab Builder v1 helps Admin and Instructor users generate a safe lab preview from a natural language prompt.

It is a preview and approval workflow only. It does not deploy Containerlab, create a `LabInstance`, or run verification.

## Access

Allowed:

- Admin
- Instructor

Blocked:

- Student

## Workflow

1. Open `AI Lab Builder`.
2. Enter a prompt describing the lab goal, nodes, protocols, and verification intent.
3. Generate a preview.
4. Review validation status, generated Containerlab YAML, generated configs, and verification rule previews.
5. Approve the preview if validation passes.
6. The system creates an inactive `LabTemplate`.
7. Review, edit, validate, and activate the template before using it in tickets.

## MVP Limits

- Categories: `Linux`, `BGP`, `OSPF`.
- Node kinds: `linux`, `frr`.
- Maximum nodes: 6.
- Maximum links: 10.
- Maximum verification rules: 10.
- Allowed images are limited to Linux and FRRouting images already accepted by template validation.
- Unsupported vendor images and `vrnetlab` images are rejected in Phase 8.

## Security Rules

- AI output is untrusted.
- Backend validates every generated LabPlan.
- Approval re-runs validation.
- Approval creates an inactive lab template only.
- AI Builder never starts Containerlab.
- AI Builder never creates lab instances.
- Students cannot use AI Builder.
- Hidden ticket solutions must not be sent to AI providers.
- AI provider API keys must come from environment variables and must not be committed.

## Environment

The feature is disabled by default.

```env
AI_LAB_BUILDER_ENABLED=false
AI_PROVIDER=openai_compatible
AI_API_BASE_URL=
AI_API_KEY=
AI_MODEL=
AI_REQUEST_TIMEOUT_SECONDS=30
AI_MAX_TOKENS=4000
```

For MVP demo without an external provider:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=mock
```

## Troubleshooting

If preview generation returns `503`, AI Lab Builder is disabled or provider configuration is missing.

If validation fails, adjust the prompt and generate a new preview. Do not manually edit preview JSON in the database.

If a student can see AI Builder navigation, treat it as a security bug and fix role-based routing/menu visibility before continuing demos.
