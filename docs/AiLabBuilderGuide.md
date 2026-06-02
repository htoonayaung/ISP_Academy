# AI Lab Builder Guide

## Purpose

AI Lab Builder v1 helps Admin and Instructor users generate a safe lab preview from a natural language prompt. Users should describe the lab in plain English; they do not need to write JSON.

It is a preview and approval workflow only. It does not deploy Containerlab, create a `LabInstance`, start a lab, or run verification.

## Access

Allowed:

- Admin
- Instructor

Blocked:

- Student

## Workflow

1. Open `AI Lab Builder`.
2. Enter a plain-language prompt describing the lab goal, nodes, protocols, and verification intent.
3. Generate a preview.
4. Review validation status, generated Containerlab YAML, generated configs, and verification rule previews.
5. Approve the preview if validation passes.
6. The system creates an inactive `LabTemplate`.
7. Review, edit, validate, and activate the template before using it in tickets.
8. Continue with the normal ticket, verification rule, student attempt, lab start, verification, and lab destroy workflow.

## MVP Limits

- Categories: `Linux`, `BGP`, `OSPF`.
- Node kinds: `linux`, `frr`.
- Maximum nodes: 6.
- Maximum links: 10.
- Maximum verification rules: 10.
- Allowed images are limited to Linux and FRRouting images already accepted by template validation.
- Unsupported vendor images and `vrnetlab` images are rejected in Phase 8.

## Natural Language Prompts

Phase 8.6 adds a backend interpreter for common simple requests. If the AI provider returns incomplete JSON but the prompt is clearly understood, the backend uses a deterministic safe scaffold and still runs full validation.

Supported simple prompts:

- `Create a two-router FRR OSPF lab with one area 0 link and an OSPF neighbor verification rule.`
- `Create a two-router FRR eBGP lab with one point-to-point link and a BGP neighbor verification rule.`
- `Create a basic Linux lab with one Alpine host named host1 and a uname verification rule.`
- `Create a two-router FRR static routing lab with one point-to-point link and a route verification rule.`

Unsupported complex labs may require more detail. Unsafe requests remain invalid.

## Security Rules

- AI output is untrusted.
- Backend validates every generated LabPlan.
- Deterministic prompt scaffolds do not bypass validation.
- Approval re-runs validation.
- Approval creates an inactive lab template only.
- Approval does not create or start a lab.
- AI Builder never starts Containerlab.
- AI Builder never creates lab instances.
- Students cannot use AI Builder.
- Hidden ticket solutions must not be sent to AI providers.
- AI provider API keys must come from environment variables and must not be committed.

## Environment

The feature is disabled by default in examples.

```env
AI_LAB_BUILDER_ENABLED=false
AI_PROVIDER=openai_compatible
AI_API_BASE_URL=
AI_API_KEY=
AI_MODEL=
AI_REQUEST_TIMEOUT_SECONDS=30
AI_MAX_TOKENS=4000
```

For the current MVP demo without an external provider:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=mock
```

Recommended real provider trial order:

1. `mock`
2. Gemini free tier
3. OpenRouter free model
4. Groq free tier
5. Paid provider only after quality is confirmed

Gemini OpenAI-compatible:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=gemini_openai_compatible
AI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
AI_API_KEY=<set-on-server-only>
AI_MODEL=gemini-2.5-flash-lite
AI_REAL_PROVIDER_CONFIRMATION_REQUIRED=true
```

OpenRouter:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=openrouter
AI_API_BASE_URL=https://openrouter.ai/api/v1
AI_API_KEY=<set-on-server-only>
AI_MODEL=openrouter/free
AI_REAL_PROVIDER_CONFIRMATION_REQUIRED=true
```

Groq:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=groq
AI_API_BASE_URL=https://api.groq.com/openai/v1
AI_API_KEY=<set-on-server-only>
AI_MODEL=llama-3.3-70b-versatile
AI_REAL_PROVIDER_CONFIRMATION_REQUIRED=true
```

Generic OpenAI-compatible:

```env
AI_LAB_BUILDER_ENABLED=true
AI_PROVIDER=openai_compatible
AI_API_BASE_URL=https://provider.example/v1
AI_API_KEY=<set-on-server-only>
AI_MODEL=<provider-model-name>
AI_REQUEST_TIMEOUT_SECONDS=60
AI_MAX_TOKENS=4000
AI_DAILY_PREVIEW_LIMIT_PER_USER=20
AI_REAL_PROVIDER_CONFIRMATION_REQUIRED=true
```

Never commit real `AI_API_KEY` values.

## Troubleshooting

If preview generation returns `503`, AI Lab Builder is disabled or provider configuration is missing.

If preview generation returns `400` with real provider confirmation text, check the UI confirmation box before submitting.

If validation fails, the preview shows a friendly explanation first and technical validation details below it. Adjust the prompt and generate a new preview. Do not manually edit preview JSON in the database.

If a student can see AI Builder navigation, treat it as a security bug and fix role-based routing/menu visibility before continuing demos.
