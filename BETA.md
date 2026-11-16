# MakerWorld Creator Stats — v0.4.3-beta2 (experimental)

## Scope

- Branch: `beta/0.4.3-scheduled-stats`. The stable `main` branch stays on 0.4.2; beta1 stays unchanged.
- Client identity: `ha-makerworld-creator-stats/v0.4.3-beta2`.
- Authenticated profile: one HTTP GET approximately every 30–31 minutes.
- Point-ledger totals: one HTTP GET approximately every 2 hours.
- Boost-token counts: one HTTP GET approximately every 2 hours.
- The two optional GETs are staggered over later profile cycles: **never more than one optional GET per scheduled profile refresh**.
- The paginated transaction-history import is still **disabled**. Rolling 7/14/30-day income sensors remain unavailable.
- Optional results are cached (only numeric counters, no access credentials). On refresh failures previously cached optional values expire after 4 hours.
- Cloudflare challenges, HTTP 429 and explicit HTTP 403 denials trigger a persistent backoff. Requests are not retried during the pause. Do not bypass rate limits.
- The initial login flow may make additional requests only when explicitly starting/re-authenticating an account.
- MakerWorld's undocumented API is not guaranteed or specifically approved for this project. Using a named User-Agent does not grant API rights.

## New diagnostic sensors

- Next profile update
- Next points update
- Next boost update
- Last successful profile update
- API connection status (`initializing`, `success`, `partial`, `paused`, `error`, `auth_required`)

These diagnostics reuse local scheduler state and do not call Bambu Lab. Their timestamps are estimates. When a protective pause is active, upcoming updates are moved to at least the end of that pause. All five are diagnostic entities on the MakerWorld device.

## HACS testing

The beta branch is **not automatically a HACS release**. To test via HACS a GitHub pre-release tagged `v0.4.3-beta2` must be published, pointing to a checked commit on this branch. If not published, use a manual branch download.

1. Back up the Home Assistant configuration. Do not install beta and stable side by side; the integration domain is shared.
2. Install the prerelease (when available) via HACS **Include prereleases → Other version**. Restart Home Assistant.
3. Confirm version `0.4.3-beta2` and check initial profile statistics.
4. Wait for scheduled point and boost updates over the following one to two hours. Do not repeatedly reload or force updates.
5. Check the five diagnostic sensors, including their pause/status behavior. Report sanitized logs only; remove tokens, emails, UID, cookies, and raw API bodies.
6. Confirm model/download/print sensors remain available if an optional endpoint returns an ordinary error, and that an access denial produces a protective pause.

## Rollback

Return to HACS prerelease `v0.4.3-beta1` and restart Home Assistant, or restore your backup. A rollback does not change Bambu's server-side access policy.

## Important caveat

No live authenticated account test is performed by the source-code changes. Repeated 403/429 is a reason to stop testing and review the API access requirements.
