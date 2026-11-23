# MakerWorld Creator Stats v0.4.4 — Stable release notes

## Summary

Stable release of the previously tested 0.4.4 beta. This release prioritizes conservative MakerWorld request scheduling and stronger handling of rejected private endpoints without expanding the API surface.

## Changes from v0.4.3

- Creator-profile refresh interval is approximately **60–61 minutes**, previously 30–31 minutes.
- Optional private points-summary and boost-token detail requests run approximately **every six hours** when enabled, previously every two hours. At most one optional endpoint is requested per profile cycle.
- New installations leave private detail requests **disabled by default**; existing installations retain their current setting.
- Profile-derived point balances, received boosts and available boost-token counts remain available without private detail requests.
- A definitive HTTP 401 from a private points or boosts endpoint suspends that endpoint for the rejected token across restarts, until successful reauthentication supplies a new token.
- HTTP 403, HTTP 429 and Cloudflare challenges continue to use protective pauses and cautious backoff.
- Transaction-history imports remain disabled. No printer control, points redemption or payout functionality is added.

## Upgrade

1. Back up your Home Assistant configuration.
2. Update MakerWorld Creator Stats through HACS / Home Assistant Marketplace to stable **v0.4.4**. Keep the existing integration entry; do not remove the integration or its devices.
3. Restart Home Assistant when prompted.
4. Review **Configure** if you want to enable optional private points and boost details. New installations have this option disabled by default; existing entries keep their saved setting.
5. Allow scheduled updates to run normally. With the one-hour profile interval, a newly received boost may take up to about an hour to appear.

## Validation

The release workflow runs offline regression tests, Python compilation, Home Assistant Hassfest and HACS / Marketplace validation. The stable release is created only after all required jobs pass. Automated tests use mocked responses and do not contact a live MakerWorld account.

The 0.4.4 code was also tested in the maintainer's Home Assistant installation before promotion to stable. This is a real-world test with one account, not a guarantee of permanent access to undocumented MakerWorld endpoints.

## API scope and safety

MakerWorld's creator statistics, points and boost endpoints are undocumented private cloud APIs. Bambu Lab has not expressly authorized these specific endpoints. The integration remains independent and unofficial, uses its own versioned client identity, makes read-only requests and does not attempt to bypass server-side restrictions. Access may be changed or denied by the service.

## Rollback

If an issue occurs, use HACS' version selector to return to stable **v0.4.3**, then restart Home Assistant. Keep your existing integration entry and configuration. Back up before changing versions.
