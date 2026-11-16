# MakerWorld Creator Stats — v0.4.3-beta3 (experimental)

## Scope

- Branch: `beta/0.4.3-marketplace`. The stable `main` branch stays on 0.4.2; Beta 2 is the development base.
- Client identity: `ha-makerworld-creator-stats/v0.4.3-beta3`.
- Authenticated profile: one HTTP GET approximately every 30–31 minutes.
- Point-ledger totals: one HTTP GET approximately every 2 hours.
- Boost-token counts: one HTTP GET approximately every 2 hours.
- The two optional GETs are staggered over later profile cycles: **never more than one optional GET per scheduled profile refresh**.
- In a healthy steady state, expect roughly three application-level reads per hour on average for one account. A refresh before the scheduled time does not send another request. The first cycle after setup or reload requests only the profile, even when both optional endpoints are overdue. Repeated reloads can still trigger extra profile reads outside a protection pause.
- The paginated transaction-history import is still **disabled**. Rolling 7/14/30-day income sensors remain unavailable.
- Optional results and retry times are cached without access credentials. On refresh failures previously cached optional values expire after 4 hours.
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

## Installation and upgrade test

The beta branch is **not automatically a HACS release**. To test via HACS a GitHub pre-release tagged `v0.4.3-beta3` must be published, pointing to a checked commit on this branch. If not published, use a manual branch download.

1. Back up the Home Assistant configuration. Do not install beta and stable side by side; the integration domain is shared.
2. In HACS, open the existing repository entry and choose **Redownload** (or **Download** on a first install). Enable prereleases if your HACS version offers the switch and select `v0.4.3-beta3` under **Need a different version?**. Restart Home Assistant once. For a branch-only build, follow the [manual installation](README.md#install-and-configure). See the [HACS version selector](https://hacs.xyz/docs/use/repositories/dashboard/#downloading-a-specific-version-of-a-repository).
3. Confirm version `0.4.3-beta2`, initial profile statistics, and the existing entity IDs used by automations. Check setup and options in English and German, including dropdown choices, translated sensor names and the six API status labels. Server-generated description attributes follow the Home Assistant system language. Raw diagnostic details and log messages use English.
4. Wait 2–3 hours to observe regular profile updates and the staggered points and boost updates. Check the five diagnostics. The 7/14/30-day income sensors should stay unavailable. Avoid repeated reloads or forced updates.
5. If an ordinary optional error occurs naturally, check for `partial` with profile statistics still available. If a denial occurs naturally, check for `paused` and a next profile time at or after the end of the pause. Stop the test after repeated denials. Do not deliberately trigger them. Report sanitized logs only and remove tokens, emails, UID, cookies, and raw API bodies.

## Rollback

If the API is paused, leave the integration disabled until the indicated pause expires before resuming tests. In HACS, use **Redownload → Need a different version? → v0.4.3-beta2** and restart Home Assistant. Keep the existing integration entry and local storage so Home Assistant retains the entity IDs and any saved pause. Restore the backup if the older version cannot be reinstalled. A backup may predate a newly recorded pause, so wait for that pause before re-enabling the integration.

## Important caveat

Offline tests cover scheduling and simulated responses. Beta 3 still needs a live Home Assistant upgrade check from Beta 2, a HACS or Marketplace installation check, and visual verification of the translations and branding. The automated checks use simulated data and do not verify Bambu API access or catalog acceptance. An initial profile failure can leave the entry in setup retry without diagnostic entities until setup succeeds. If local storage fails, the active pause is kept in memory and is only guaranteed until Home Assistant restarts.
