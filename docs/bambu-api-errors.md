# Bambu-API: Fehler 403 und Cloudflare

Untersucht am 10. November 2026. Die Fälle stammen aus greghesp/ha-bambulab und belegen nicht die konkrete Ursache unseres bisher nur als HTTP 403 erfassten Fehlers.

## Bestätigte Unterschiede

- [Issue 692](https://github.com/greghesp/ha-bambulab/issues/692): Cloudflare blockierte auch den API-Anmeldeendpunkt. Der Wechsel zu cloudscraper in [PR 698](https://github.com/greghesp/ha-bambulab/pull/698) war ein erster Lösungsversuch.
- [Issue 702](https://github.com/greghesp/ha-bambulab/issues/702): Der erste Ansatz half nicht dauerhaft bzw. nicht in allen Umgebungen. Der Entwickler berichtete Unterschiede zwischen WSL und Home-Assistant-Container. Nach dem nächsten Update v2.0.33 meldeten mehrere Nutzer Erfolg; China-Anmeldung blieb bei anderen betroffen. [PR 709](https://github.com/greghesp/ha-bambulab/pull/709) führte curl_cffi für ein browserähnlicheres Verbindungsverhalten ein. Diese Berichte zeigen keinen universellen Fix.
- [PR 738](https://github.com/greghesp/ha-bambulab/pull/738), zusammengeführt am 15. November 2024: Laut Entwickler waren Bambu/Cloudflare-Regeln wieder gelockert. Rückkehr zu cloudscraper, auch weil curl_cffi auf manchen 32-Bit-Systemen nicht verfügbar war. Fehlerarten wurden getrennt behandelt. Daraus folgt keine feste automatische Sperrdauer.
- [PR 804](https://github.com/greghesp/ha-bambulab/pull/804), zusammengeführt am 25. Dezember 2024: Mehrere Drucker konnten viele Slicer-Einstellungsabfragen kurz hintereinander aus derselben IP auslösen. Der Entwickler benennt Cloudflare-Drosselung als Ursache und begrenzt die Abfrage auf einmal je erfolgreicher Druckerverbindung. Das ist ein belegter Burst-Fall, kein Beleg für ein bestimmtes zulässiges MakerWorld-Abfrageintervall.
- [PR 2058](https://github.com/greghesp/ha-bambulab/pull/2058), zusammengeführt am 1. August 2026: HTTP 403 mit JSON-Grund `missing_cookie` war eine separate CSRF-Anforderung am Website-Endpunkt für Zwei-Faktor-Anmeldung. Lösung: auf E-Mail-/SMS-Code-Anmeldung über api.bambulab.com wechseln. Der Autor dokumentiert einen erfolgreichen Test mit einem europäischen 2FA-Konto. Unsere Integration nutzt bereits direkt die API-E-Mail-Code-Anmeldung und ruft den betroffenen Website-Endpunkt nicht auf.
- [PR 1758](https://github.com/greghesp/ha-bambulab/pull/1758), zusammengeführt am 7. Dezember 2025: Ein vermeintlicher Anmeldefehler kam von ungültig komprimierten Brotli-Daten. Änderung auf gzip/deflate. Kein Beleg für die Ursache eines tatsächlichen HTTP 403.

## Was nach einer Sperre passiert

Die geprüften Berichte dokumentieren erfolgreiche Wiederherstellung durch Updates sowie gelockerte Schutzregeln. Eine garantierte Freigabe nach Stunden oder Tagen, einen allgemein gültigen Punkte-Abfragegrenzwert oder eine automatische dauerhafte Kontosperre belegen sie nicht. Ein funktionierender Browser auf demselben Anschluss widerlegt eine Client-Schutzprüfung nicht; auch die Laufzeitumgebung unterschied sich in Issue 702.

[Cloudflare dokumentiert](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/) Challenge Pages als HTML-Antworten mit Prüfung der Browserumgebung. Regeln können aus WAF, Bot Management oder Rate Limiting stammen. Der [Header cf-mitigated: challenge](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/detect-response/) ist ein ausdrückliches Challenge-Signal. `Server: cloudflare` und `CF-Ray` allein zeigen dagegen nur die Beteiligung von Cloudflare an der Antwort.

## Umsetzung in 0.4.1

- Fehlernummer plus eigener, fest vorgegebener Name des abgefragten Bereichs.
- Cloudflare nur bei Challenge-Header oder klaren Cloudflare-Merkmalen in einer HTML-Antwort diagnostizieren.
- HTTP 429, fehlendes CSRF-Cookie, HTTP 401 und sonstigen HTTP 403 getrennt behandeln.
- Höchstens 8192 Antwortbytes für 403/429 prüfen; keine Servertexte, Cookies, Tokens, IP-Adressen oder vollständigen Antworten in Fehler übernehmen.
- Bei Cloudflare/429 während einer optionalen Statistikabfrage keine weiteren optionalen Abfragen oder den Transaktionsimport im selben Durchlauf starten.
- Keine automatische neue Anmeldung allein aufgrund eines HTTP 403; keine automatische Umgehung einer Challenge.

Die Erkennung verbessert die Diagnose, behebt aber keine serverseitige Sperre. Bestehende Aktualisierungs- und Home-Assistant-Einrichtungswiederholungen wurden in diesem Update nicht neu gestaltet. Ein späteres Update kann eine gemeinsame, neustartfeste Abfragepause mit begrenzter Auswertung von Retry-After ergänzen.
