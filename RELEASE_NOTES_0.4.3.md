# MakerWorld Creator Stats 0.4.3 — Stable release notes

## Summary

This release replaces the previously impersonated OrcaSlicer client identity
with our own transparent, versioned `ha-makerworld-creator-stats/v0.4.3`
identifier. It brings the successfully tested Beta 4 functionality to a
stable release without expanding the undocumented MakerWorld API surface.

## Improvements

- Uses the distinct `ha-makerworld-creator-stats` client name and
  `homeautomation` type in all API requests; version follows the manifest.
- Scheduled read-only profile refresh approximately every 30–31 minutes;
  point-ledger summaries and boost-token counters approximately every 2 hours
  each, staggered to avoid bursts.
- Separate cached summary counters, restart/reload request guards,
  persistent cooldowns for access denials, challenges and HTTP 429.
- Five diagnostic sensors: next profile/points/boost refresh, last successful
  profile update and API connection status.
- English and German UI strings and custom project artwork.
- Preserves existing account configuration and technical sensor unique IDs.

## Functional change relative to stable 0.4.2

**Rolling 7-, 14- and 30-day income sensors are unavailable in 0.4.3.**
Importing the full transaction history could cause excessive API requests, so
that import is disabled. Existing sensor entities remain registered under
their previous unique IDs, but their value is unavailable. Lifetime point
income and expense totals remain available via the compact point summary.

## Bambu Lab third-party cloud policy

In its [12 November 2026 announcement](https://forum.bambulab.com/t/a-postmortem-on-this-weeks-cloud-traffic-anomaly/262567), Bambu Lab confirmed
that certain non-critical, read-only third-party cloud monitoring may
continue within reasonable limits and recommended distinct client identities.
**The announcement does not expressly authorize these undocumented MakerWorld
creator/account endpoints.** This integration is an independent community
project; it is not officially supported or endorsed. The server may restrict
or revoke access. Do not evade service restrictions.

## Upgrade

1. Back up the Home Assistant configuration. Do not remove the existing
   MakerWorld integration entry.
2. Once the GitHub **stable release** `v0.4.3` is published, select
   that version via HACS/Marketplace. Keep prereleases disabled.
3. Restart Home Assistant once. Verify profile counts, point balances,
   boost counters, and the five diagnostic entities.
4. Let scheduled refreshes run naturally; do not repeatedly reload to
   accelerate the test. Stop repeated testing after a 403 or 429.
5. Confirm automations still refer to the same entity IDs. Historical income
   sensors will be unavailable until a safer import is implemented.

## Rollback

If an urgent rollback is required, back up the configuration and select
`v0.4.3-beta4` or the previously installed release via the HACS version
selector, then restart. An older version such as 0.4.2 impersonates OrcaSlicer
and is **not recommended for continued cloud use**. Do not clear stored pause
files or force requests through a server denial. Keep access tokens private.

## Validation

The source includes offline regression tests and GitHub Actions workflows
for Python checks, Hassfest and HACS. This note does not itself certify
that any workflow passed or that Bambu Lab approved the endpoints.
