# MakerWorld Creator Stats

![Unofficial MakerWorld Creator Stats icon](custom_components/makerworld_creator_stats/brand/icon.png)

[Deutsch](README.de.md)

MakerWorld Creator Stats is an independent Home Assistant integration for the signed-in creator's statistics, point balances, and boosts. It estimates gift card credit and USD cash rewards in Home Assistant using the data already fetched.

## Beta 4

Beta 4 adds protection against repeated profile requests during setup failures or integration reloads. It includes English and German setup, options, sensor names, and status labels. The purple chart icon is project artwork. Home Assistant 2026.3 and later can display branding packaged with a custom integration.

| Area | What you can see |
| --- | --- |
| Creator profile | Published models, model and print-profile downloads and prints, likes, collections, followers, following and level |
| Points and boosts | Regular and exclusive balances, lifetime points earned and spent, and boost activity |
| Reward estimates | Gift card equivalents and estimated USD cash rewards, based on your selected terms |
| Diagnostics | Last successful profile update, next scheduled updates, and API connection status |

Rolling 7-, 14-, and 30-day income sensors stay unavailable in this beta. Their entities are retained for existing installations. Reward estimates are calculated locally. Redemption, eligibility and payouts are handled by MakerWorld.

## Install and configure

1. Back up your Home Assistant configuration. For an upgrade, keep the existing integration entry.
2. **HACS:** In **⋮ → Custom repositories**, add `https://github.com/Retropurp/ha-makerworld-creator-stats` as **Integration** and download it. The HACS version selector shows Beta 4 once a corresponding GitHub prerelease exists. Enable prereleases if your HACS version offers the option.
3. **Home Assistant Marketplace:** Use the [custom repository link](https://my.home-assistant.io/redirect/hacs_repository/?owner=Retropurp&repository=ha-makerworld-creator-stats&category=integration). The Marketplace checks the repository and version it installs. For an unreleased branch build, use the manual steps below.
4. Restart Home Assistant. For a new installation, go to **Settings → Devices & services → Add integration → MakerWorld Creator Stats**. Enter the email address of your global Bambu account and the one-time code delivered by Bambu Lab.
5. Use **Configure** to select reward sensor groups, your shop region, and gift card terms. Deselecting a reward group removes its entities from the registry. Dashboards and automations that use those entities may need updating.

For a manual Beta 4 test, download the branch snapshot and copy the entire `custom_components/makerworld_creator_stats` folder to `/config/custom_components/makerworld_creator_stats`, replacing the previous integration files. Restart Home Assistant and follow the setup steps for a new installation. See [BETA.md](BETA.md) for upgrade checks and rollback.

## Data and availability

The integration uses undocumented Bambu Lab endpoints for global accounts. API authorization for this project is unconfirmed. Bambu Lab, MakerWorld and Home Assistant have not endorsed the integration. The email address and access token are stored in Home Assistant's local configuration. Keep backups private.

Profile updates normally run every 30–31 minutes. Points and boost requests have separate approximately two-hour schedules, staggered with at most one optional request per profile cycle. A cold start without an active pause reads the profile only. Reloads during the current profile interval reuse in-memory data. Profile failures use a two-hour retry interval, also during setup. Cached optional values can survive failures for up to four hours after their last successful update. HTTP 403, HTTP 429 and Cloudflare challenges can trigger persistent protection pauses. Check the diagnostic timestamps before retrying.

## Further reading

- [Beta test checklist and rollback](BETA.md)
- [Detailed German documentation](README.de.md)
- [Reward values and regional examples](docs/forum-findings-and-reward-values.md)
- [Third-party attribution](THIRD_PARTY.md)
- [License](LICENSE)
