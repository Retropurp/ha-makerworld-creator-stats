# Community findings and regional gift card values

**Research date:** 10 November 2026  
**Primary source:** [Live stats app for MakerWorld models analytics](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976), Bambu Lab community forum.

This document records research sources, historical third-party observations, and assumptions used to design reward estimates. It is **not** a statement of official MakerWorld terms or API authorization.

At the time of research, 149 publicly accessible posts from the thread were obtained through the topic listing and subsequently loaded post IDs. Post numbering includes gaps and ends at 155. Linked media and external websites were not exhaustively reviewed. Claims about another application are attributed to its developer or users rather than independently reproduced.

## Regional gift card examples

[Forum post #40, 10 April 2026](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/40) reported the following point-store offers, repeated in posts #62 and #66. With the exception described below, these are **historical community reports**, not confirmed current offers.

| Region reported in forum | Currency | Reported credit | Reported point cost | Project status |
| --- | --- | ---: | ---: | --- |
| United States | USD | 40 | 490 | Experimental |
| European Union | EUR | 40 | 524 | Maintainer-verified on 10 November 2026 |
| United Kingdom | GBP | 35 | 535 | Experimental |
| Canada | CAD | 55 | 504 | Experimental |
| Australia | AUD | 65 | 511 | Experimental |
| Japan | JPY | 5,300 | 502 | Experimental |
| Asia, including Singapore, Thailand, Malaysia, Hong Kong, Macao, and Taiwan | USD, inferred from report | 40 | 490 | Experimental; verify currency |
| South Korea | KRW | 58,000 | 490 | Experimental |

The EU example was checked in the maintainer's point store on 10 November 2026; this does not establish its availability in other accounts or at later dates. Every preset remains user-editable.

The forum's China-related rewards were Youzan discount offers, not a verified cash-value gift card. Accordingly, **no China gift card equivalent is configured** in the integration. China-account sign-in is separately unsupported.

## Point categories and calculations

[Post #36](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/36) cautioned against assuming that regular points are always used for gift cards and exclusive points always for cash. Later [posts #88 and #89](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/88) described selecting either regular points or regular plus exclusive points when estimating gift cards.

The integration makes this basis explicit. It separates the **current available balance** from **lifetime earned points**, which include points spent in the past. Reward conversions are labelled estimates at the **current selected rate**, not confirmed historical redemption value.

The standard gift card calculations include estimated balance value, estimated lifetime earnings, affordable whole gift cards, credit represented by whole cards, points missing to the next card, and progress to the next card. They use decimal arithmetic to avoid floating-point errors at threshold boundaries.

USD cash rewards are calculated separately from gift card terms, using the exclusive-point rate and payout thresholds documented in the main [README](../README.md). Currency exchange rates, gift card terms, and cash rates are **not interchangeable**.

## Region preferences

In [posts #62](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/62) and [#66](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/66), the third-party developer reported detecting preferred shop regions after sign-in. The thread did not identify a reliable field or API endpoint for doing so.

This integration therefore requires an **explicit store choice**. Interface language, time zone, and global-vs-China API region do not reliably establish the user's gift card store. Automatic region detection should only be implemented after validating the actual account data and retaining a manual override.

## Timeline data and history

Early [posts #10](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/10) and [#47](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/47) described capturing counts locally from installation. Later [posts #89](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/89) and [#93](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/93) described historical Creator Center data, including model and print-profile analytics, available to another application. An older statement that history was unavailable should therefore not be generalized to all clients or later versions.

[Post #16](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/16) described UTC day boundaries and a delayed point credit recorded near 22:00 UTC. This may have changed and requires verification before any calendar-day feature is developed.

Current MakerWorld Creator Stats rolling earnings sensors use point-transaction **booking timestamps** for the previous 7, 14, and 30 rolling 24-hour periods. These are not official Creator Center daily reports. Point credits applied late are attributed to their booking timestamp. Expense transactions are not deducted from earned amounts.

The transaction history importer was subsequently implemented and tested with one actual account. The original design notes about this feature being 'not yet implemented' no longer apply.

## Robustness and user reports

Other discussion posts identified failure cases worth considering in testing:

- [Posts #102–#104](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/102): Incomplete responses, large model inventories, zero balances, and failed refreshes. Always distinguish unavailable data from an actual zero; display stale data only when clearly marked.
- [Posts #105–#112](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/105): Account-security changes and usernames containing periods reportedly affected another application's account handling. Prefer stable account identifiers and test special characters. The precise root cause was not independently established.
- [Posts #115–#123](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/115): Service outages and region-dependent recovery. A temporary failure should not be interpreted as deleted content or a deleted account.
- [Post #101](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/101): Milestone notifications should establish an initial baseline to avoid notifying for earlier activity.

## Request frequency and authentication research

[Posts #73–#77](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/73) discussed Android background refresh timing. [Post #28](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/28) reported more frequent foreground than background updates on iOS. These app-observation intervals are **not** evidence of an allowable API rate for third-party account polling.

[Post #87](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/87) described a third-party application's browser-based sign-in using a stored session cookie. That is an observation about another client, not a proven or approved authentication alternative for this Home Assistant integration. The present implementation uses the API's email verification-code flow and does not import browser cookies.

Avoid exposing access tokens in issue reports, diagnostics, or Home Assistant backups. See [API access and error research](bambu-api-errors.md) for the project's actual defensive polling strategy.

## Possible future enhancements

The referenced discussion suggested savings goals, longer time series, per-model analytics, print-profile insights, commissions, and trending rankings. Such features would need separate endpoint research and data validation. In particular, [posts #53 and #54](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/54) indicated that rankings may depend on view and personalization; any ranking sensor must specify exactly what it represents.

A future implementation of daily statistics must distinguish Home Assistant's time zone from MakerWorld's booking time, account for daylight-saving changes and delayed refreshes, and avoid falsely attributing an entire change since the last poll to the current day.

## API terms and permission remain unresolved

[Forum posts #137](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/137) and [#140](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/140) recount a different developer's report that Bambu Lab declined a proposed API use. This is a historical third-party account, not a legally authoritative determination about this repository.

No official API approval for **MakerWorld Creator Stats** is documented. Discussion evidence and successful local tests do not establish permission or a stable API contract. A direct, mutually agreed access route should be resolved before making stronger compatibility or support claims.

---

This file is retained as an **evidence and design-notes record**. The current product behavior and versioned limitations are described in the [README](../README.md).
