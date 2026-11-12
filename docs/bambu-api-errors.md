# Bambu Lab API: HTTP 403, Cloudflare and rate limiting

**Research date:** 10 November 2026  
**Scope:** Public reports from [greghesp/ha-bambulab](https://github.com/greghesp/ha-bambulab) and the defensive behavior implemented in MakerWorld Creator Stats.

The incidents below establish that multiple denial modes have affected Bambu Lab clients. **They do not establish the root cause of any specific HTTP 403 observed by this integration**, and do not grant permission to use the undocumented API.

## Evidence from other integrations

- [Issue #692](https://github.com/greghesp/ha-bambulab/issues/692): Cloudflare also blocked an API sign-in endpoint. [PR #698](https://github.com/greghesp/ha-bambulab/pull/698) initially attempted an alternative HTTP client.
- [Issue #702](https://github.com/greghesp/ha-bambulab/issues/702): The first fix was not consistently successful; reports differed between WSL and a Home Assistant container. Some users reported success after release v2.0.33, while China-region sign-in remained problematic. [PR #709](https://github.com/greghesp/ha-bambulab/pull/709) introduced `curl_cffi`. The reports do **not** demonstrate a universal solution.
- [PR #738](https://github.com/greghesp/ha-bambulab/pull/738), merged 15 November 2024: A maintainer described relaxed Bambu/Cloudflare rules and returned to `cloudscraper`, partly because `curl_cffi` was unavailable on some 32-bit systems. Error cases were differentiated. No fixed lockout duration was established.
- [PR #804](https://github.com/greghesp/ha-bambulab/pull/804), merged 25 December 2024: Bursts of slicer-setting requests from multiple printers sharing one IP address were identified as a possible Cloudflare throttling trigger. The change limited requests to once per successful printer connection. This is a documented burst scenario, **not** evidence for an allowed MakerWorld polling interval.
- [PR #2058](https://github.com/greghesp/ha-bambulab/pull/2058), merged 1 August 2026: An HTTP 403 with JSON reason `missing_cookie` represented a CSRF requirement at a website 2FA endpoint. The fix switched to the API's email/SMS-code sign-in. The author reported success with a European 2FA account. MakerWorld Creator Stats already uses the API email-code path rather than the affected website endpoint.
- [PR #1758](https://github.com/greghesp/ha-bambulab/pull/1758), merged 7 December 2025: A sign-in-like failure was traced to invalid Brotli content and addressed by switching to gzip/deflate. This does not explain a genuine HTTP 403.

## Distinguishing denial types

Cloudflare [documents challenge pages](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/) as HTML that performs browser-related checks. The response header [`cf-mitigated: challenge`](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/detect-response/) explicitly indicates a challenge.

By contrast, a response containing only `Server: cloudflare` or `CF-Ray` does **not** prove that Cloudflare blocked the request; those headers can also occur on successful API responses.

The integration therefore distinguishes:
- HTTP 401: Explicit authentication rejection; Home Assistant requests reauthentication.
- HTTP 429: Rate limiting, with support for a valid `Retry-After` value.
- HTTP 403 with an explicit Cloudflare challenge header or recognizable challenge HTML.
- HTTP 403 with an identified `missing_cookie` CSRF reason.
- Other HTTP 403 responses with an **undetermined** cause.

Diagnostic messages include a fixed, locally defined name for the affected area (account profile, point totals, boost tokens, or transaction history). Only the first **8 KiB** of a denial response is inspected for classification. Server-provided bodies, tokens, cookies, and email addresses are not copied into error messages.

A successful browser request from the same connection does not rule out client-specific API restrictions. The reviewed reports document occasional recovery after upstream changes, but **no guaranteed time to unblock, formal API quota, or automatic permanent account ban**.

## Implemented in v0.4.1

- Distinguish Cloudflare challenges, rate limiting, CSRF requirements, authentication errors, and unknown HTTP 403 responses.
- Avoid labelling all HTTP 403 errors as either invalid credentials or Cloudflare blocks.
- Stop the current polling cycle if an optional request hits Cloudflare protection or HTTP 429.
- Avoid repeatedly requesting new email codes after a protection denial.
- Avoid automatic challenge bypass, browser-cookie extraction, and token rotation.

These measures improve error identification and reduce unnecessary requests; they do not remove server-side restrictions.

## Backoff policy in v0.4.2

The implementation was informed by other clients, but it does **not** assume Bambu Lab publishes a specific request quota:

- [HACS](https://github.com/hacs/integration/blob/main/custom_components/hacs/base.py) honors `Retry-After` for downloads while limiting individual waits and retry counts. Those short download retries are not suitable for a continuing API access denial.
- [Home Assistant Tado coordinator](https://github.com/home-assistant/core/blob/dev/homeassistant/components/tado/coordinator.py) adjusts requests using a known quota and reset time. No comparable confirmed MakerWorld quota is available.
- [Daikin Onecta](https://github.com/jwillemsen/daikin_onecta/blob/master/custom_components/daikin_onecta/daikin_api.py) separates rate-limit state from ordinary connectivity failures.
- [Home Assistant 2026.11.0 coordinator](https://github.com/home-assistant/core/blob/2026.11.0/homeassistant/helpers/update_coordinator.py) supports `UpdateFailed.retry_after` during initial setup. The [earlier implementation note](https://contributors.home-assistant.io/blog/2025/11/17/retry-after-update-failed/) documents differences in older versions. MakerWorld Creator Stats additionally enforces its own stored deadline before initiating statistics requests.

| Condition | Local policy |
| --- | --- |
| Normal account refresh | 30 minutes plus up to 60 seconds of jitter |
| Transaction history | At most once every six hours |
| Repeated explicit Cloudflare restrictions | 2, 4, 8, then 12 hours (capped) |
| HTTP 429 | 30 minutes, then exponentially increasing to 12 hours |
| Valid longer `Retry-After` header | Honor up to 24 hours, including jitter |

The pause is stored per configuration entry as a deadline, strike count, and fixed reason **without credentials**. It remains active across Home Assistant reloads and restarts. The strike counter resets after a successful statistics refresh.

Cloudflare or HTTP 429 during history import pauses the account's polling cycle. The importer is retried after the pause, subject to normal scheduling. There is no blocking long sleep or immediate retry loop.

If the stored pause cannot be read, the integration defers requests rather than making an unprotected call. If saving fails, the in-memory pause remains active but may not persist after a restart, and an explicit diagnostic message is shown.

Other integrations and account entries have independent request paths; this project cannot enforce a global per-IP or per-account quota across them.

## Unresolved questions

1. Is there a supported, explicitly permitted API or alternative way to obtain the required MakerWorld creator statistics?
2. Which exact request patterns, credentials, or client conditions trigger the observed denials?
3. What access, quota, and authentication requirements are acceptable to Bambu Lab for community integrations?

Until these are resolved, backoff should be viewed as a **protective measure**, not proof of reliability or authorization.
