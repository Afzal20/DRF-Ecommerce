# 3. Provider-Agnostic AI Gateway

Date: 2026-09-01

## Status

Accepted

## Context

We want to integrate AI capabilities such as text generation, search embeddings, and chat. Relying directly on a single API (like OpenAI) in our business logic makes us vulnerable to outages and locks us into their pricing structure.

## Decision

We will build an AI gateway interface (`generate_text`, `embed`, `chat`) and inject the specific provider adapter via settings. All AI calls will run through background tasks (Celery) with fallbacks and rate limits.

## Consequences

- Core operations are decoupled from external AI APIs.
- AI features fail gracefully.
- Reduced risk of vendor lock-in.
