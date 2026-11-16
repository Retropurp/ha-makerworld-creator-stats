# Third-party cloud access: public statement and project-specific limits

Bambu Lab's [12 November 2026 postmortem](https://forum.bambulab.com/t/a-postmortem-on-this-weeks-cloud-traffic-anomaly/262567) says it has
accommodated third-party software accessing parts of its private cloud where
safe. It explicitly allows continued access to certain non-critical
monitoring capabilities, such as printer status and temperature, within
reasonable usage limits. It may restrict access to protect service
availability and recommends third-party clients identify themselves rather
than claiming to be OrcaSlicer or another official client.

**Our integration** is an independent, read-only Home Assistant client for
the signed-in creator's MakerWorld profile, point summary and boost-token
counts. We identify as `ha-makerworld-creator-stats/v<version>` and use
scheduled queries, caching and persisted rate-limit protections. We do not
control printers, start prints, redeem rewards or initiate payments.

**The distinction:** Bambu Lab's statement does **not** explicitly list the
private MakerWorld creator-profile, point-ledger or boost endpoints used here.
No public API contract, specific rate quota, formal authorization or
long-term compatibility guarantee for these endpoints has been confirmed.
The statement's mention of MakerWorld as a cloud service is not itself an
authorization for every MakerWorld API.

For that reason this project does not present itself as an official Bambu
Lab integration, does not promise unrestricted access, and does not
circumvent denials or Cloudflare challenges. HTTP 403/429 and challenges
trigger protective pauses. Configuration and backups must be treated as
private because they may contain an access token.

**Primary source:** Bambu Lab Team, "A Postmortem on This Week's Cloud
Traffic Anomaly", Bambu Lab Community Forum, 12 November 2026.
