# Beta test — MakerWorld Creator Stats 0.4.3-beta1

> Experimental and unofficial. Bambu Lab / MakerWorld has not approved the
> undocumented profile API for this project. A user-agent identifies software;
> it does not grant API rights. Respect server denials, do not bypass controls.

## Scope and identity

- Branch: `beta/0.4.3-client-id`. Stable `main` stays at 0.4.2.
- User-Agent: `ha-makerworld-creator-stats/v0.4.3-beta1`.
- Client Name: `ha-makerworld-creator-stats` (no OrcaSlicer impersonation).
- The version is read from `custom_components/makerworld_creator_stats/manifest.json`.
- Scheduled polling: one authenticated GET to
  `https://api.bambulab.com/v1/design-user-service/my/profile`, approximately
  every 30–31 minutes after a successful refresh.
- Additional point ledger, boost right, and 30-day history requests: **disabled**
  in this diagnostic beta. Previously cached history is not loaded.
- Explicit first-time sign-in / reauthentication still sends the separate
  email-code/login requests and validates the authenticated profile.

## Expected sensors

Creator counts, level, followers, likes, collections, account-reported point
balances and boosts received are parsed from the creator profile when present.
Transaction totals, detailed used/expired boost tokens, and rolling 7/14/30-day
income calculations are unavailable in this beta. Local gift-card or USD
estimates may still work from profile point balances, but calculations needing
transaction totals will remain unavailable. Sensor unique IDs are unchanged.
A missing/denied profile also makes profile-derived values unavailable.

## How to test with Home Assistant

1. Do **not** overwrite a working stable installation without a backup. The beta
   and stable share the same Home Assistant integration domain and cannot be
   installed side by side under one Home Assistant configuration.
2. For a manual beta install, use the files from this **beta branch**, copy
   `custom_components/makerworld_creator_stats` to the Home Assistant
   `/config/custom_components/` directory, and restart Home Assistant.
   Alternatively, select a beta/pre-release in HACS **only if it is published**;
   a branch by itself is not a HACS release.
3. Confirm the installed `manifest.json` version is `0.4.3-beta1`. If a
   previous Cloudflare-protection pause is stored, allow it to expire; do not
   manipulate the pause cache or repeatedly reload to avoid the pause.
4. Use the existing account entry. If first-time authentication is required,
   request an email code once using the built-in flow. Never share tokens.
5. Inspect the MakerWorld integration and Home Assistant logs for successful
   profile updates or the precise failure type. Redact emails, IDs, tokens,
   cookies, and any raw response bodies before sharing.
6. Do not repeatedly retry denied requests. HTTP 401 suggests reauthentication;
   HTTP 403/429 may indicate Bambu access restrictions or rate limits.

## What counts as a successful test?

A working signed-in profile with realistic nonzero creator statistics after a
normal scheduled refresh demonstrates that this configuration can retrieve
that account's profile under those conditions. It **does not** demonstrate
authorization or future API availability. No live test was run as part of
preparing this branch.

## Rollback

Restore the stable `0.4.2` integration directory and restart Home Assistant.
If using HACS, return to a stable release. Keep backups of Home Assistant
configuration private because they may contain access tokens.
