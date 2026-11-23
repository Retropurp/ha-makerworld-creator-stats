# MakerWorld Creator Stats v0.4.5-beta.1

**Pre-release / test build** from `beta/0.4.5-diagnostics`. This is a follow-up beta based on the Home Assistant-tested 0.4.4 code.

## Changes from 0.4.4-beta.1

- Adds diagnostic sensors for the last successful private points update and boost update.
- Adds diagnostic sensors identifying which endpoint triggered an active protection pause and the classified reason (`cloudflare`, `throttled`, or `denied`).
- Reuses existing coordinator state only. These diagnostics do **not** make additional MakerWorld requests and do not expose credentials or raw server response bodies.
- Keeps the conservative profile cadence (60–61 minutes), private detail cadence (six hours), one optional request per profile cycle, and existing 401 / 403 / 429 / Cloudflare protections unchanged.

## Validation

This beta is prepared for offline regression tests, Hassfest, HACS / Marketplace validation, and then a Home Assistant smoke test. No live MakerWorld credentials or production API calls are used by CI.

## Installation

Do not install until the beta validation workflow passes and the prerelease is published. Back up Home Assistant first. Update the integration in HACS / Marketplace with beta versions enabled, then restart Home Assistant. Existing config entries and entity IDs are intended to remain unchanged; the four new diagnostic entities will be added.

## Safety

MakerWorld private endpoints are undocumented. This project does not bypass Cloudflare challenges, import transaction history, redeem points, or control printers. Diagnostics report locally observed state only.
