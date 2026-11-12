# MakerWorld Creator Stats

A community-maintained Home Assistant integration for MakerWorld account statistics, points, boosts, and locally calculated reward estimates.

**Project version:** 0.4.2 · **Integration type:** Cloud polling · **Status:** Unofficial / experimental API access

> [!IMPORTANT]
> **Unofficial project.** MakerWorld Creator Stats is developed independently and is not affiliated with, endorsed by, or officially supported by Bambu Lab, MakerWorld, or the Home Assistant project. The integration uses undocumented Bambu Lab endpoints. No authorization for this API access has been confirmed. Successful tests with one account do not establish long-term availability or permission to use these interfaces.

The integration reads statistics associated with the signed-in account and calculates local dashboard estimates. It does **not** control printers, redeem gift cards, initiate payout requests, or modify MakerWorld account data. Monetary values are estimates, **not** records of actual payments.

## Current status

As of **12 November 2026**, account sign-in, profile statistics, points, boost data, reward calculations, transaction history import, and sensor-group selection were successfully exercised in the maintainer's Home Assistant installation with one real account.

Subsequent operation encountered HTTP 403 denials and Cloudflare challenges. Version 0.4.2 improves diagnosis and limits repeated requests, but it **cannot bypass a server-side restriction or guarantee uninterrupted access**. A stable and mutually agreed access method with Bambu Lab / MakerWorld has not been established.

Automated unit tests use simulated responses and Home Assistant components. The live test above must not be interpreted as multi-account, multi-region, or long-duration validation.

## Features

### Account statistics

The integration exposes **25 base sensors**:

| Category | Included values |
| --- | --- |
| Downloads | Model downloads, print-profile downloads, combined downloads |
| Prints | Model prints, print-profile prints, combined prints |
| Profile | Published models, likes, collections, followers, following, account level |
| Point balances | Total, regular, and exclusive points |
| Point transactions | Regular and exclusive lifetime earnings and spending, plus combined totals |
| Boosts | Received boosts, available tokens, used tokens, expired tokens |

Combined download/print sensors add the model and print-profile counts. Missing components result in an unavailable combined value rather than an invented total. Lifetime earnings include points that have subsequently been spent.

Optional calculated sensors provide estimated gift card values, USD cash-reward values, and rolling 7-, 14-, and 30-day earnings. These are computed locally from shared fetched data; they do not introduce separate API polling.

### Reward sensor groups

Select the desired calculated sensors under **Settings → Devices & services → MakerWorld Creator Stats → Configure**:

| Mode | Exposed calculations |
| --- | --- |
| Gift cards only | Gift card estimates and corresponding 7-, 14-, and 30-day equivalents |
| USD cash rewards only | USD estimates, payout thresholds, and exclusive-point earnings |
| Both | Both sets of calculations |

The 25 base sensors remain available regardless of the selected mode. Settings are stored per account. Changing the mode reloads the integration and removes disabled calculated sensors from the entity registry; existing dashboard cards and automations referencing these sensors may need attention. Re-enabled sensors retain their original unique IDs.

## Installation

<!-- ha-marketplace:exclude-start -->

### Home Assistant 2026.11 and later: Marketplace

1. Open **Settings → Marketplace** in Home Assistant.
2. Select **Add from link** and enter:
   `https://github.com/Retropurp/ha-makerworld-creator-stats`
3. Connect GitHub if prompted. If the repository type is not detected, select **Integration**.
4. Open the repository page and install **MakerWorld Creator Stats**.
5. Restart Home Assistant if requested, then open **Settings → Devices & services → Add integration**.
6. Search for **MakerWorld Creator Stats** and complete the sign-in flow.

The repository is available as a **custom Marketplace repository**; that is not an official listing or endorsement.

### Earlier Home Assistant installations: HACS

In HACS, add `https://github.com/Retropurp/ha-makerworld-creator-stats` under **Custom repositories** with category **Integration**, install the integration, restart Home Assistant, and add it under **Settings → Devices & services**.

### Manual installation

1. Copy `custom_components/makerworld_creator_stats` to `/config/custom_components/makerworld_creator_stats`.
2. Restart Home Assistant.
3. Add **MakerWorld Creator Stats** under **Settings → Devices & services**.
4. Enter your Bambu Lab account email address and the one-time verification code sent by Bambu Lab.

<!-- ha-marketplace:exclude-end -->

### Sign-in and supported regions

Sign-in uses an email address and one-time code; enter the code **only** in your Home Assistant interface. The integration currently targets global accounts through `api.bambulab.com`. Mainland China accounts are **not** supported by this configuration and require a different API implementation.

HTTP 401 triggers the Home Assistant reauthentication flow. An account identifier mismatch is rejected during reauthentication. A blocked API request (HTTP 403 / Cloudflare) is **not** treated as proof that a password or token is wrong.

### Language support

The default translation source is English (`strings.json`). German is provided in `translations/de.json`, and English in `translations/en.json`. Home Assistant displays translated names and setup labels according to the UI language. Technical sensor keys and existing unique IDs do not change as a result of localization; previously customized entity names and entity IDs can remain unchanged.

## Gift card estimates

Gift card estimates are enabled by choosing a store region, the points basis, and the reward terms. Regular points or regular plus exclusive points may be included. A custom offer can be configured by specifying its currency, face value, and point cost.

The **EU example — EUR 40 of store credit for 524 points — was verified by the maintainer on 10 November 2026**. Other regional presets were gathered from community reports dated 10 April 2026 and remain experimental. Always verify the current offering in your own MakerWorld point store; no preset establishes current availability or eligibility.

Six calculated sensors cover:

- Estimated current point-balance value and estimated lifetime-earnings value.
- Number and value of affordable **whole** gift cards.
- Additional points needed for the next full gift card and progress toward it.

Example: at the EU example rate, 800 eligible points represent an estimated prorated value of EUR 61.07, but only **one whole EUR 40 gift card** is affordable. Another 248 points would be needed for the next whole gift card.

The integration does not check shop inventory, redemption eligibility, or previously redeemed rewards. Calculations use the currently configured rate; historical earnings are not a ledger of actual voucher payouts.

See [regional presets and community findings](docs/forum-findings-and-reward-values.md).

## USD cash-reward estimates

Exclusive points are converted using **USD 0.066 per exclusive point**, with an estimated minimum payout request of **USD 100** and maximum of **USD 1,000 per request**. The eligible amount is additionally limited by the available total point balance. These terms were observed by the maintainer on 10 November 2026; MakerWorld still reviews actual requests.

Six calculated sensors provide the estimated current USD value, estimated lifetime earnings, estimated claimable amount, missing USD and points to reach the minimum, and progress toward that minimum.

Displayed USD amounts are truncated to two decimal places. The minimum threshold is evaluated using the unrounded value; missing points are rounded upward to three decimals. **No payment is requested or made.**

## Transaction history and rolling earnings

Rolling sensors calculate positive points credited during the preceding **7, 14, or 30 days**, using the **booking timestamp** of each transaction. Spending is not deducted. A credit posted today for earlier work is counted on the date it was booked, not when the underlying activity occurred.

The history importer:
- Uses the same authenticated point-transaction endpoint as the lifetime point totals.
- Fetches up to **100 transactions per page**, at most **50 pages**, and runs within a **two-minute timeout**.
- Imports up to 30 days of history when available, then attempts a refresh no more often than every **six hours**, subject to the global protection pause.
- Validates all fetched pages before replacing the previous complete set; incomplete, unexpectedly structured, or inconsistent history is rejected instead of guessed.
- Stores only minimal transaction timestamps and amounts in the Home Assistant storage directory. It does not store credentials or model names in the history cache.

The attributes `history_error` and `history_synced_at` describe the latest history error and last successful import (Unix timestamp). If a usable complete history is unavailable, the rolling sensors become unavailable; they do not silently report zero or display stale values as current. History-based cash and gift-card values use the currently configured rates rather than historical exchange rates.

These derived financial estimates intentionally do not enable long-term Home Assistant statistics across changing currencies or reward terms. Ordinary state history depends on the Recorder configuration.

## Polling, errors, and backoff

| Condition | Implemented behavior |
| --- | --- |
| Normal account polling | Approximately every 30 minutes, plus up to 60 seconds of random offset |
| Transaction history | At most once every six hours |
| Ordinary profile request failure | Increase account refresh interval to two hours |
| Explicit Cloudflare challenge | Pause account statistics for 2, 4, 8, then at most 12 hours |
| HTTP 429 rate limiting | Start with a 30-minute pause, increasing to at most 12 hours |
| Valid longer `Retry-After` | Honor it up to a maximum 24-hour pause |
| HTTP 401 | Request reauthentication |
| Other HTTP 403 or a CSRF-related denial | Diagnose separately; do not assume that Cloudflare or invalid credentials are the cause |

All timings are **conservative local policies**, not published Bambu Lab API quotas or guarantees that a block will expire. There is no confirmed universal unblocking time.

The pause state contains only a deadline, failure counter, and fixed reason. It is saved per configuration entry and restored across reloads and Home Assistant restarts. No account statistics request is sent while a pause is active. If storage cannot be read, the integration fails closed rather than immediately retrying. If writing the pause fails, the pause remains active in memory but may not survive a restart. An additional pause applies when an optional request or the history importer encounters Cloudflare or HTTP 429.

The integration does not bypass challenges, rotate identities, automatically reauthenticate after HTTP 403, or ingest browser cookies. Requests from other integrations and other accounts are not centrally rate-limited by this project.

Read the [API error investigation](docs/bambu-api-errors.md) for background, external reports, and implementation rationale.

## Data access and security

Sign-in stores the email address and access token in Home Assistant's local configuration. **This is not a separately encrypted credential vault.** Anyone who can access Home Assistant's configuration or backups may be able to extract that token. A Bambu Lab token may have capabilities beyond the read-only API calls used by this integration.

Requests made by this integration use HTTPS with certificate verification to `api.bambulab.com`; redirects are disabled. The destination, HTTP methods, and paths are constrained in code:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/v1/user-service/user/sendemail/code` | Request email verification code |
| POST | `/v1/user-service/user/login` | Exchange verification code for token |
| GET | `/v1/design-user-service/my/profile` | Account and profile statistics |
| GET | `/v1/point-service/point-bill/my?offset=0&limit=1&filter=all` | Lifetime point totals |
| GET | `/v1/point-service/point-bill/my?offset=N&limit=100&filter=all` | Paginated point history (bounded N) |
| GET | `/v1/point-service/boost/boostingright` | Boost tokens |

Diagnostic errors use locally defined messages and never include raw API response bodies, cookies, email addresses, or access tokens. For denied requests the classification logic inspects only a bounded **8 KiB** response prefix. Nevertheless, keep logs and Home Assistant backups private and redact any credentials before reporting a problem.

## Limitations and compatibility

- MakerWorld API access remains undocumented, unofficial, and may be blocked without notice. No API authorization or stability commitment is confirmed.
- Global accounts only; China-region login requires separate implementation.
- A successful single-account test is not a guarantee for other accounts, geographies, API changes, or long-term operation.
- Creator Center data such as impressions, traffic sources, daily impressions, and individual-model analytics are **not** currently included.
- Reward values are indicative, configurable calculations. They do not certify eligibility, shop inventory, cash receipts, or redemption.
- Disabled calculated sensor groups are removed from the entity registry when options change. Existing automation and dashboard references must be reviewed before disabling them.

## Testing and development

Regression tests cover reward calculations, transaction parsing and accumulation, API error classification, and stored backoff behavior, including simulated Home Assistant reloads and restarts. The test suite can be run with:

```sh
python -m unittest discover -s tests -v
```

Automated tests use synthetic fixtures; they do not contact MakerWorld. A successful test run validates local behavior only, not live access, API permission, or every Home Assistant deployment.

**Before a wider release**, complete repeatable checks on real Home Assistant versions, reauthentication, sensor-registry behavior, and long-duration operation. Do not attempt to work around access restrictions when investigating failures.

## Licensing and attribution

This project includes code derived from [greghesp/ha-bambulab](https://github.com/greghesp/ha-bambulab), licensed under MIT. See [THIRD_PARTY.md](THIRD_PARTY.md) and [LICENSE](LICENSE) for origin and licensing details.

Additional technical references:
- [Home Assistant configuration flows](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [Home Assistant data polling](https://developers.home-assistant.io/docs/integration_fetching_data/)
- [Home Assistant integration translations](https://contributors.home-assistant.io/core/integrations/translations/)
- [Home Assistant Marketplace](https://www.home-assistant.io/integrations/marketplace/)

For problems, report reproducible behavior in [GitHub Issues](https://github.com/Retropurp/ha-makerworld-creator-stats/issues) without publishing credentials or unredacted API responses.
