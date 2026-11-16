# MakerWorld Creator Stats

![Unofficial MakerWorld Creator Stats icon](custom_components/makerworld_creator_stats/brand/icon.png)

[Deutsch](README.de.md)

MakerWorld Creator Stats is an independent Home Assistant integration for the signed-in creator's statistics, point balances, and boosts. It estimates gift card credit and USD cash rewards in Home Assistant using the data already fetched.

## Beta 0.4.4 – API traffic safeguards (unreleased)

This beta reduces the profile refresh interval from every 30–31 minutes to **60–61 minutes** and private point/boost details from every 2 hours to **6 hours** (with only one optional request on a profile cycle). New installations leave private detail endpoints **off** until explicitly enabled through Configure; existing entries keep them enabled unless you opt out. Profile-derived point balances, received boosts and available boost tokens work without these additional requests. A definitive HTTP 401 from either private endpoint suspends that endpoint until a *new authentication token* is provided, including across restarts. Cloudflare/403/429 responses continue to use cautious backoff. Transaction-history imports remain disabled.

This version is experimental. Test it using the linked draft PR; it is **not** the stable release.

## Stable 0.4.3

Version 0.4.3 replaces the former OrcaSlicer-identifying requests with our own versioned client identity, `ha-makerworld-creator-stats/v0.4.3`. It includes conservative polling, backoff and persisted retry deadlines, protections against repeated requests on startup or reload, and English/German interface translations. The purple chart icon is original project artwork; it is not Bambu Lab branding.

**Important change from 0.4.2:** The 7-, 14-, and 30-day rolling income sensors remain registered but are unavailable because bulk transaction-history imports are disabled to reduce requests. See [release notes](RELEASE_NOTES_0.4.3.md).

| Area | What you can see |
| --- | --- |
| Creator profile | Published models, model and print-profile downloads and prints, likes, collections, followers, following and level |
| Points and boosts | Regular and exclusive balances, lifetime points earned and spent, and boost activity |
| Reward estimates | Gift card equivalents and estimated USD cash rewards, based on your selected terms |
| Diagnostics | Last successful profile update, next scheduled updates, and API connection status |

Lifetime totals come from the lightweight point-ledger summary; the 7-, 14-, and 30-day rolling income sensors remain unavailable. Their existing entity IDs are retained. Reward estimates are calculated locally; redemption, eligibility and payouts are handled by MakerWorld.

## Install and configure

1. Back up your Home Assistant configuration. For an upgrade, keep the existing integration entry.
2. **HACS:** In **⋮ → Custom repositories**, add `https://github.com/Retropurp/ha-makerworld-creator-stats` as **Integration**. After the GitHub `v0.4.3` stable release is published, choose that version (with prereleases disabled) and download it.
3. **Home Assistant Marketplace:** Use the [custom repository link](https://my.home-assistant.io/redirect/hacs_repository/?owner=Retropurp&repository=ha-makerworld-creator-stats&category=integration). The Marketplace checks the repository and version it installs. For an unreleased branch build, use the manual steps below.
4. Restart Home Assistant. For a new installation, go to **Settings → Devices & services → Add integration → MakerWorld Creator Stats**. Enter the email address of your global Bambu account and the one-time code delivered by Bambu Lab.
5. Use **Configure** to select reward sensor groups, your shop region, and gift card terms. Deselecting a reward group removes its entities from the registry. Dashboards and automations that use those entities may need updating.

For manual installation, use the tagged `v0.4.3` source (once published) and copy the entire `custom_components/makerworld_creator_stats` folder to `/config/custom_components/makerworld_creator_stats`, replacing previous integration files. Restart Home Assistant, retaining the existing configuration entry. Back up your configuration first. See [release notes](RELEASE_NOTES_0.4.3.md) for changes and rollback.

## Third-party cloud access and project status

On 12 November 2026, [Bambu Lab publicly explained](https://forum.bambulab.com/t/a-postmortem-on-this-weeks-cloud-traffic-anomaly/262567) that third-party software may continue to use certain safe, non-critical cloud capabilities, particularly read-only printer monitoring, within reasonable usage limits. Bambu Lab also encourages third-party clients to identify themselves rather than impersonating an official application. This project follows that guidance with its own versioned client identity, read-only statistics requests and conservative scheduling.

**Scope matters:** Bambu Lab did not explicitly confirm that its statement covers this integration's undocumented MakerWorld creator-profile, point-ledger and boost endpoints. These are private cloud APIs, not a supported public MakerWorld API contract. Access may be limited, changed or denied. Our project is independent and not endorsed by Bambu Lab, MakerWorld or Home Assistant. Learn more in [Third-party API access and limitations](docs/third-party-cloud-access.md).

Your email address and access token are stored in Home Assistant's local configuration. Keep backups private.

Profile updates normally run every 60–61 minutes. If enabled, private points and boost requests have separate approximately six-hour schedules, staggered with at most one optional request per profile cycle. A cold start without an active pause reads the profile only. Reloads during the current profile interval reuse in-memory data. Profile failures use a two-hour retry interval, also during setup. Cached optional values can survive failures for up to four hours after their last successful update. HTTP 403, HTTP 429 and Cloudflare challenges can trigger persistent protection pauses. Check the diagnostic timestamps before retrying.

## Further reading

- [Stable v0.4.3 release notes and rollback](RELEASE_NOTES_0.4.3.md)
- [Third-party cloud access and limitations](docs/third-party-cloud-access.md)
- [Historical Beta 4 test checklist](BETA.md)
- [Detailed German documentation](README.de.md)
- [Reward values and regional examples](docs/forum-findings-and-reward-values.md)
- [Third-party attribution](THIRD_PARTY.md)
- [License](LICENSE)
