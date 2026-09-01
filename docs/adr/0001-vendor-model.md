# 1. Multi-Vendor Model

Date: 2026-09-01

## Status

Accepted

## Context

The current application is a single-vendor storefront. We need to support multiple vendors selling their products on the same platform, which requires segregating products, orders, and payouts by vendor.

## Decision

We will introduce a `Vendor` model linked one-to-one with a platform user (owner). We will also introduce a `VendorMembership` table to allow future staff access per vendor. Role-based access control (RBAC) will be used to enforce boundaries, and a `VendorOrder` model will split orders for individual fulfillment.

## Consequences

- All catalog models must be scoped by vendor.
- Security requires strict object-level permissions to avoid IDOR.
- Payout calculations will become more complex and require a ledger or payout model.
