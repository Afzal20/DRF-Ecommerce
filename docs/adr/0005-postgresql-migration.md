# 5. PostgreSQL Migration

Date: 2026-09-01

## Status

Accepted

## Context

The current application uses SQLite, which does not support concurrent write traffic efficiently and lacks robust locking mechanisms (like `SELECT ... FOR UPDATE`) needed for atomic stock decrementing during multi-vendor checkout.

## Decision

We will migrate the primary database to PostgreSQL for staging and production environments. SQLite may still be used for rapid local testing if no locking is required, but PostgreSQL is the target standard.

## Consequences

- Requires Docker compose for local development to match production setup.
- Enables safe concurrent checkouts and advanced features like `pgvector` for AI search.
