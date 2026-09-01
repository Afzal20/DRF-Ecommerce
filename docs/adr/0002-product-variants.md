# 2. Product Variants

Date: 2026-09-01

## Status

Accepted

## Context

Currently, the `Cart` model uses free-text fields for `size` and `color`. This prevents accurate stock tracking per variant (e.g. knowing if a "Large, Red" shirt is in stock vs a "Small, Blue" one).

## Decision

We will consolidate `ItemSize` and `ItemColor` into a single `ProductVariant` model. This model will hold the specific size, color, price adjustments, and stock quantity for each combination. Orders and Carts will reference the `ProductVariant` foreign key.

## Consequences

- Improved inventory tracking and validation.
- Requires data migration for existing items.
