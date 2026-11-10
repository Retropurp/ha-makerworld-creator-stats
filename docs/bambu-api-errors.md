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

Die Erkennung in 0.4.1 verbessert die Diagnose, behebt aber keine serverseitige Sperre.

## Vergleich und Entscheidung für 0.4.2

- [HACS](https://github.com/hacs/integration/blob/main/custom_components/hacs/base.py) behandelt in seinem Downloadpfad HTTP 429 durch Auswertung von Retry-After, begrenzt die einzelne Wartezeit dort auf 60 Sekunden und die Versuchszahl auf fünf. Das passt zu kurzen Downloads; für eine anhaltende Cloudflare-Ablehnung unserer Statistikabfragen ist das zu aggressiv.
- [Tado in Home Assistant](https://github.com/home-assistant/core/blob/dev/homeassistant/components/tado/coordinator.py) berechnet Abstände anhand verbleibender API-Aufrufe und der Zeit bis zum erwarteten Quoten-Reset. Ein vergleichbares bestätigtes Bambu-Kontingent haben wir nicht; daher keinen Tages-Reset oder Grenzwert erfinden.
- [Daikin Onecta](https://github.com/jwillemsen/daikin_onecta/blob/master/custom_components/daikin_onecta/daikin_api.py) trennt Rate-Limit-Zustand von allgemeinen Verbindungsfehlern, führt Anfragen über eine gemeinsame Sperre und zeigt ausgeschöpfte Kontingente als Reparaturhinweise. Die Trennung der Fehlerarten übernehmen wir; druckerspezifische Steuerungslogik ist für unsere Statistikabfragen nicht erforderlich.
- Der [Home-Assistant-Coordinator](https://github.com/home-assistant/core/blob/2026.11.0/homeassistant/helpers/update_coordinator.py) unterstützt UpdateFailed.retry_after und überträgt es ab Core 2026.11 auch auf den ersten fehlgeschlagenen Aufbau. [Ältere Beschreibung](https://contributors.home-assistant.io/blog/2025/11/17/retry-after-update-failed/) weist ausdrücklich darauf hin, dass das beim ersten Aufbau noch nicht galt. Deshalb zusätzlich vor jedem Statistikdurchlauf eine eigene, gespeicherte Deadline prüfen; so entstehen selbst bei früheren lokalen Setup-Wiederholungen keine Serveranfragen während der Pause.

Entscheidung: regulär 30 Minuten plus bis zu 60 Sekunden zufälliger Versatz. Verlauf höchstens alle sechs Stunden. Cloudflare-Pause 2/4/8/12 Stunden, wiederholt maximal zwölf Stunden; HTTP 429 startet bei 30 Minuten und verdoppelt sich bis zwölf Stunden. Längere gültige Retry-After-Angaben (Sekunden oder HTTP-Datum) berücksichtigen, jedoch auf 24 Stunden begrenzen. Den Zeitversatz ebenfalls auf das 24-Stunden-Maximum begrenzen.

Pausen werden pro Konfigurationseintrag im Home-Assistant-Speicher abgelegt und im laufenden Home Assistant zusätzlich über Neuladen hinweg gehalten. Gespeichert werden ausschließlich Deadline, Fehlerzähler und feste Fehlerkategorie. Neuladen verlängert die Pause nicht und umgeht sie nicht. Nach erfolgreicher Aktualisierung Zähler zurücksetzen. Eine Sperre beim Verlaufsimport unterbricht den gesamten Durchlauf; nach der Pause wird dieser Import erneut versucht.

Keine blockierenden langen Sleeps und keine sofortige Retry-Schleife. Keine automatisch neue Anmeldung, rotierende Identitäten oder Übernahme von Browser-Cookies. Wenn die Pause nicht lesbar ist, zunächst ohne Netzabfragen warten. Wenn Speichern fehlschlägt, im laufenden Prozess weiter pausieren und ausdrücklich auf die fehlende Neustart-Persistenz hinweisen. Die normale Drucker-Integration und weitere Kontoeinträge besitzen eigene Abfragewege, die wir damit nicht steuern.

Diese Wahl reduziert Last und vermeidet wiederholtes Anfragen während einer erkannten Sperre. Sie garantiert weder eine Freigabe noch verhindert sie jede zukünftige Schutzprüfung. Die Bambu-Grenzwerte bleiben unbekannt.
