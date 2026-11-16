# MakerWorld Creator Stats v0.4.4-beta.1

**Pre-release / test build** from `beta/0.4.4-api-guardrails`. The stable `v0.4.3` is unchanged. **Do not install this as a stable release.**

## Changes from v0.4.3

- MakerWorld creator-profile polling now runs every **60–61 minutes**, previously every 30–31 minutes.
- Private points summary and boost-token detail endpoints run at most once each approximately **every six hours** when enabled, previously every two hours.
- **New accounts default to private detail requests disabled**; configure the integration to opt in. Existing installations retain private detail requests until switched off.
- MakerWorld profile supplies the balance, received boosts and available boost-token counts even with private details disabled.
- A definitive **HTTP 401 from a private points or boosts endpoint disables that endpoint for the rejected token** across restarts until successful reauthentication changes the token. HTTP 403 / 429 and Cloudflare challenges continue to trigger protective pauses.
- Transaction-history imports remain disabled; there is no printer control or points redemption functionality.
- Added regression tests for throttling, opt-out, token rejection and restart recovery, plus updated English/German UI strings.

## Install with HACS / Home Assistant Marketplace

1. Back up Home Assistant first. Keep the existing MakerWorld Creator Stats integration entry; **do not remove the integration or its devices**.
2. In HACS / the Home Assistant Marketplace, open **MakerWorld Creator Stats**, choose the re-download / version selector (often in the three-dot menu), turn on **Show beta versions**, then choose `v0.4.4-beta.1`. If prerelease selection is not offered, use the manual method below.
3. Restart Home Assistant. In **Settings → Devices & services → MakerWorld Creator Stats → Configure**, inspect the **private points and boost details** option.
4. Confirm existing boost and profile entities keep their entity IDs. Check the connection-status and next-update diagnostic sensors. A 60-minute interval means boost notifications may arrive up to about an hour after receiving the boost.

**Manual alternative:** Download the source ZIP for this tagged prerelease; copy the entire `custom_components/makerworld_creator_stats` folder to `/config/custom_components/makerworld_creator_stats`, replacing the previous component folder (but **do not delete existing Home Assistant config entries**), then restart HA.

## Validation and safety

GitHub Actions runs offline unit tests, Hassfest and HACS/Marketplace validation before the prerelease is created. No live MakerWorld account or production cloud API was used in automated testing.

MakerWorld private API endpoints are undocumented; no formal API authorization or permanent service availability is implied. This is an independent, unofficial project that identifies itself with its own versioned User-Agent and does not bypass Cloudflare challenges. For source review, see [draft PR #4](https://github.com/Retropurp/ha-makerworld-creator-stats/pull/4).

## Rollback

Install stable `v0.4.3` using HACS' version selector and restart Home Assistant. Existing entities and your saved configuration entry should be preserved. Follow the backup step before either direction.
