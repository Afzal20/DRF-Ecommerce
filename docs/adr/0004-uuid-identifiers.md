# 4. Opaque Identifiers (UUIDs)

Date: 2026-09-01

## Status

Accepted

## Context

Sequential integer IDs on models like `Order`, `Cart`, and `Vendor` make it easy for attackers to enumerate resources or guess order volumes (a form of information disclosure).

## Decision

We will switch to UUIDs (or ULIDs) as primary keys or public identifiers for all public-facing resources. Slugs will be used for SEO-friendly URLs where applicable (like products).

## Consequences

- Prevents resource enumeration.
- Database keys are slightly larger and less index-friendly than sequential integers, but the security trade-off is worth it.
