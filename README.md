# MakerWorld Creator Stats

[Deutsch](README.de.md)

MakerWorld Creator Stats is an independent Home Assistant community integration that reads the signed-in creator's MakerWorld statistics and calculates reward estimates locally. The integration on this branch is version 0.4.2.

## Project status

The integration is unofficial. Bambu Lab, MakerWorld, and Home Assistant have not endorsed it. It uses undocumented Bambu Lab endpoints. On 12 November 2026, the maintainer contacted Bambu Lab to ask whether a supported, authorized API is available for this use. Authorization is pending.

The maintainer previously tested sign-in, account statistics, transaction history, and reward estimates on one real account. Subsequent requests for the authenticated account profile returned HTTP 403. The cause of the denial remains unconfirmed. The maintainer has paused polling on the test installation while awaiting clarification.

## What it shows

- **Creator statistics:** published models, downloads and prints for models and print profiles, likes, collections, followers, and creator level.
- **Account statistics:** regular and exclusive points, points earned and spent, and boost activity.
- **Local estimates:** gift-card equivalents, estimated USD reward equivalents, and points earned over 7, 14, and 30 days where transaction data is available.

Reward values are estimates based on the configured rates and available data. The integration reads statistics only. It has no features for controlling printers, redeeming rewards, or initiating payouts.

## Data access

Home Assistant uses the Bambu account email and a one-time code to obtain a token. Home Assistant stores the email and token in its local configuration. Keep configuration backups private. This version supports global Bambu accounts. China-region accounts require a separate implementation.

The integration normally refreshes account statistics about every 30 minutes and imports transaction history at most every six hours. It backs off when it detects a Cloudflare challenge or rate limiting. Calculated sensors reuse fetched data. When requests fail, affected sensors report unavailable. Avoid repeatedly reloading the integration or requesting new sign-in codes after an access denial.

## Installation

The current version can be installed as a **custom HACS repository**. In HACS, open **⋮ → Custom repositories**, add `https://github.com/Retropurp/ha-makerworld-creator-stats` with type **Integration**, and download **MakerWorld Creator Stats**. Restart Home Assistant, then open **Settings → Devices & services → Add integration**. Setup depends on successful access to the Bambu account profile.

For manual installation, copy `custom_components/makerworld_creator_stats` into Home Assistant's `/config/custom_components/`, restart Home Assistant, and add the integration from **Devices & services**.

## Further reading

- [Detailed German documentation](README.de.md)
- [Reward values and regional examples](docs/forum-findings-and-reward-values.md)
- [Third-party attribution](THIRD_PARTY.md)
- [License](LICENSE)
