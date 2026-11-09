# MakerWorld Creator Stats

Eigenständige Home-Assistant-Integration für 25 MakerWorld-Kontowerte. Version 0.1.0, erste lokal geprüfte Fassung.

## Installation über HACS

In HACS unter **⋮ → Benutzerdefinierte Repositories** die Adresse `https://github.com/Retropurp/ha-makerworld-creator-stats` als Typ **Integration** hinzufügen. **MakerWorld Creator Stats** herunterladen, Home Assistant neu starten und unter **Einstellungen → Geräte & Dienste** hinzufügen. Spätere Releases erscheinen als Updates.

## Manuelle Installation

1. Den Ordner `custom_components/makerworld_creator_stats` aus diesem Paket nach `/config/custom_components/makerworld_creator_stats` auf deinem Home Assistant kopieren.
2. Home Assistant neu starten.
3. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **MakerWorld Creator Stats** suchen.
4. Deine Bambu-Konto-E-Mail-Adresse eingeben und den von Bambu zugesandten Anmeldecode bestätigen. Den Code ausschließlich in deiner Home-Assistant-Oberfläche eingeben.
5. Die Sensoren erscheinen unter einem eigenen MakerWorld-Gerät. Alle 25 sind standardmäßig aktiviert.

Die Fassung nutzt globale Bambu-Konten auf `api.bambulab.com`. Konten der chinesischen Region benötigen eine Anpassung. Die Integration verwendet die aktuellen Home-Assistant-Schnittstellen für `ConfigEntry.runtime_data` und erneute Anmeldung.

## Enthaltene Werte

| Bereich | Sensoren |
| --- | --- |
| Downloads | Modelle, Druckprofile, kombiniert |
| Drucke | Modelle, Druckprofile, kombiniert |
| Profil | Veröffentlichte Modelle, Likes, Sammlungen, Follower, gefolgte Konten, Level |
| Punktestand | Gesamt, regulär, exklusiv |
| Punktebewegungen | Regulär verdient und ausgegeben, exklusiv verdient und ausgegeben, insgesamt verdient und ausgegeben |
| Boosts | Erhalten, verfügbare Tokens, verwendete Tokens, verfallene Tokens |

Die kombinierten Downloads und Drucke addieren Modell- und Druckprofilwerte. MakerWorld zeigt auf der Profilseite die Modellwerte. Fehlende Bestandteile werden beim Kombinieren als nicht verfügbar behandelt. Punktebewegungen sind die von Bambu gelieferten Kontosummen.

Diese Fassung deckt die bekannten Kontostatistiken der drei im Quellprojekt verwendeten Statistik-Endpunkte ab. Creator-Center-Auswertungen wie Impressionen, Aufrufe, Besucherquellen, Tageswerte und Einzelstatistiken pro Modell erfordern weitere Schnittstellen und sind noch offen.

## Anmeldung und Datenzugriff

Die Anmeldung nutzt E-Mail-Adresse und Einmalcode. Home Assistant speichert anschließend E-Mail-Adresse und Zugangstoken in seiner lokalen Konfiguration. Dieser Speicher ist keine separate verschlüsselte Passwortablage. Wer Konfiguration oder Backups lesen kann, kann möglicherweise auch den Token auslesen. Der Bambu-Token kann weitergehende Kontorechte besitzen, auch wenn diese Integration ausschließlich Statistiken abfragt.

Alle durch diese Integration ausgelösten HTTP-Anfragen gehen über HTTPS an `api.bambulab.com`. Die Zertifikatsprüfung bleibt aktiviert. Weiterleitungen sind deaktiviert. Die erlaubten Ziele und Methoden sind im Code festgelegt.

| Methode | Pfad | Zweck |
| --- | --- | --- |
| POST | `/v1/user-service/user/sendemail/code` | Anmeldecode anfordern |
| POST | `/v1/user-service/user/login` | Code gegen Token tauschen |
| GET | `/v1/design-user-service/my/profile` | Profil- und Kontowerte |
| GET | `/v1/point-service/point-bill/my?offset=0&limit=1&filter=all` | Summen der Punktebewegungen |
| GET | `/v1/point-service/boost/boostingright` | Boost-Tokens |

Die Abfrage erfolgt alle 15 Minuten. Nach einem Fehler der Profilabfrage steigt der Abstand auf zwei Stunden. Fehler einzelner Zusatzabfragen führen zu nicht verfügbaren Werten für die betroffenen Sensoren. Bei HTTP 401 fordert Home Assistant eine erneute Anmeldung an. Einen neuen Code kannst du im Anmeldedialog ausdrücklich anfordern. Eine abweichende Konto-ID wird bei der erneuten Anmeldung abgewiesen.

Die Anwendung selbst schreibt keine Anmeldeinformationen, API-Antworten oder Tokens in Protokolle. Sensible Werte gehören auch beim Teilen von Home-Assistant-Backups und Fehlerberichten geschützt. Bei manueller Installation erfolgt das Update durch Austausch der Dateien.

## Prüfstand

Die Prüfung verwendet künstliche API-Antworten für Datenverarbeitung, HTTP-Verhalten und Fehlerfälle. Die Fassung wurde noch nicht in einer laufenden Home-Assistant-Installation mit einem echten Bambu-Konto getestet. Insbesondere kann Bambu die automatisierte Anmeldung oder Abfragen durch Bot-Schutz blockieren. Ein erfolgreicher Live-Test bleibt erforderlich.

## Quellen

- [ha-bambulab und MakerWorld-Erweiterung](https://github.com/greghesp/ha-bambulab/pull/2143)
- [Home-Assistant-Konfigurationsdialoge](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [Home-Assistant-Datenabfragen](https://developers.home-assistant.io/docs/integration_fetching_data/)

Hinweise zur übernommenen Datenverarbeitung stehen in `THIRD_PARTY.md`.
