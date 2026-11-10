# MakerWorld Creator Stats

Eigenständige Home-Assistant-Integration für 25 MakerWorld-Kontowerte. Version 0.4.2.

## Abfragehäufigkeit und Schutzpausen

Kontostatistiken werden ungefähr alle 30 Minuten aktualisiert, mit bis zu einer Minute zufälligem Zeitversatz. Der Transaktionsverlauf wird höchstens alle sechs Stunden importiert. Alle darauf basierenden Rechensensoren verwenden diese gemeinsam geladenen Daten und erzeugen keine eigenen API-Abfragen.

Bei erkannter Cloudflare-Sperre pausieren die Statistikabfragen des betroffenen Kontos zunächst zwei Stunden, bei weiteren gesperrten Versuchen vier, acht und höchstens zwölf Stunden. Bei HTTP 429 beginnt die Pause bei 30 Minuten und verdoppelt sich ebenfalls bis maximal zwölf Stunden. Eine längere gültige Retry-After-Servervorgabe kann die Pause auf höchstens 24 Stunden verlängern. Ein zufälliger Zeitversatz von bis zu einer Minute kommt hinzu, ohne das 24-Stunden-Limit zu überschreiten. Diese Zeiten sind unsere vorsichtige Strategie, keine bestätigten Bambu-Grenzwerte oder Freigabeversprechen.

Die Pause samt Fehlerzähler wird ohne Zugangsdaten lokal gespeichert. Neuladen und Home-Assistant-Neustart umgehen eine gespeicherte Pause nicht. Nach Ablauf erfolgt automatisch ein neuer Versuch; nach erfolgreicher Aktualisierung beginnt die normale Frequenz wieder. Auch eine Sperre beim Transaktionsimport hält weitere Statistikabfragen an. Home Assistant zeigt den frühesten Wiederholungszeitpunkt ausdrücklich in UTC an. Während fehlgeschlagener Aktualisierungen sind betroffene Sensoren nicht verfügbar; alte Werte werden nicht als frisch ausgegeben.

Kann eine Pause nicht gespeichert werden, bleibt sie im laufenden Home Assistant aktiv und die Fehlermeldung weist darauf hin. Bei unlesbarem Pausenspeicher starten vorsichtshalber keine Statistikabfragen. Bewusst gestartete Anmeldungen sind von dieser Statistikpause getrennt. Andere Integrationen und Konten können weiter eigene Anfragen erzeugen.

## Verbindungsfehler verstehen

Ab Version 0.4.1 nennt eine abgewiesene Anfrage auch den betroffenen Bereich, beispielsweise Kontoprofil oder Transaktionsverlauf. Die Erkennung unterscheidet eine ausdrücklich erkennbare Cloudflare-Schutzseite, ein fehlendes CSRF-Cookie, HTTP 429 (Anfragebegrenzung) und einen nicht näher erklärbaren HTTP 403. Ein Cloudflare-Serverheader allein beweist keine Sperre. Antworttexte, Cookies und Zugangsdaten werden nicht in Fehlermeldungen übernommen; zur Einordnung wird höchstens ein 8-KiB-Antwortpräfix geprüft.

Eine erkannte Schutzprüfung wird dadurch nicht aufgehoben. Es gibt keine bestätigte allgemeine Wartezeit bis zur Freigabe. Bei Schutzsperren nicht ständig neu laden oder neue Anmeldecodes anfordern. Bei eindeutig abgewiesenem Zugangstoken (HTTP 401) fordert Home Assistant eine erneute Anmeldung an. Weitere Hinweise und Quellen: [Untersuchung der Bambu-Fehlerberichte](docs/bambu-api-errors.md).

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

Die Abfrage erfolgt ungefähr alle 30 Minuten. Nach einem sonstigen Fehler der Profilabfrage steigt der Abstand auf zwei Stunden; bei Cloudflare und HTTP 429 gilt die oben beschriebene gespeicherte Schutzpause. Fehler einzelner Zusatzabfragen führen zu nicht verfügbaren Werten für die betroffenen Sensoren. Bei HTTP 401 fordert Home Assistant eine erneute Anmeldung an. Einen neuen Code kannst du im Anmeldedialog ausdrücklich anfordern. Eine abweichende Konto-ID wird bei der erneuten Anmeldung abgewiesen.

Die Anwendung selbst schreibt keine Anmeldeinformationen, API-Antworten oder Tokens in Protokolle. Sensible Werte gehören auch beim Teilen von Home-Assistant-Backups und Fehlerberichten geschützt. Bei manueller Installation erfolgt das Update durch Austausch der Dateien.

## Prüfstand

Die Prüfung verwendet künstliche API-Antworten für Datenverarbeitung, HTTP-Verhalten und Fehlerfälle. Die Fassung wurde noch nicht in einer laufenden Home-Assistant-Installation mit einem echten Bambu-Konto getestet. Insbesondere kann Bambu die automatisierte Anmeldung oder Abfragen durch Bot-Schutz blockieren. Ein erfolgreicher Live-Test bleibt erforderlich.

## Quellen

- [ha-bambulab und MakerWorld-Erweiterung](https://github.com/greghesp/ha-bambulab/pull/2143)
- [Home-Assistant-Konfigurationsdialoge](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [Home-Assistant-Datenabfragen](https://developers.home-assistant.io/docs/integration_fetching_data/)

Hinweise zur übernommenen Datenverarbeitung stehen in `THIRD_PARTY.md`.


## Guthaben-Gutscheinrechner ab 0.2.0

Nach der Installation unter **Einstellungen → Geräte & Dienste → MakerWorld Creator Stats → Konfigurieren** die Shopregion und Punktebasis auswählen. Bei vorhandenen Installationen ist zunächst kein Shop ausgewählt. Die sechs zusätzlichen Rechensensoren werden verfügbar, sobald eine gültige Konfiguration vorliegt. Änderungen wirken direkt auf die Sensoren.

Die EU-Vorlage mit 40 EUR für 524 Punkte wurde am 10. November 2026 durch den Nutzer im Shop bestätigt. Die weiteren Vorlagen sind experimentelle Community-Angaben vom 10. April 2026. Währung, Guthaben und Punktekosten vor dem Speichern mit dem eigenen Punkteshop vergleichen. Alle Werte sind überschreibbar. Benutzerdefinierte Angebote sind ebenfalls möglich. Für China ist in dieser Quelle kein Guthaben-Angebot belegt.

Die sechs Sensoren zeigen den rechnerischen Gegenwert des aktuellen Punktekontos und der bisher verdienten Punkte, die finanzierbare ganze Gutscheinanzahl, deren Guthaben, fehlende Punkte und den Fortschritt zum nächsten Gutschein. Die Punktebasis ist wahlweise regulär oder regulär plus exklusiv. Die Auswahl gilt für beide Gegenwerte.

Guthabenwerte werden zum konfigurierten Kurs berechnet. Einlösbarkeit, Bestand im Shop und tatsächlich erhaltenes Gutschein-Guthaben werden dadurch nicht geprüft. Nach einer exakt erreichten Schwelle startet der Fortschritt zum folgenden Gutschein wieder bei null. Fehlende Punkte beziehen sich dann auf einen weiteren vollständigen Gutschein.

Die Sensoren benötigen keine zusätzlichen Bambu-Abfragen. Die Punktebasis, die gewählten Konditionen und der Quellenstand stehen in den Sensorattributen. Für die Rechensensoren ist keine Langzeitstatistikklasse gesetzt, damit ein späterer Wechsel der Währung oder des Kurses keine vermischten Geldstatistiken erzeugt. Die normale Zustandshistorie hängt vom Recorder ab.

[Quellen und regionale Vorlagen](docs/forum-findings-and-reward-values.md)


## USD-Auszahlung und Einnahmen ab 0.3.0

Sechs zusätzliche USD-Sensoren zeigen den Gegenwert exklusiver Punkte, den USD-Gegenwert der bisher verdienten exklusiven Punkte, den rechnerisch beantragbaren Betrag, fehlende USD und Punkte sowie den Fortschritt zur Mindestauszahlung. Es gelten 0,066 USD je exklusivem Punkt, mindestens 100 USD und höchstens 1.000 USD pro Antrag. Der verfügbare exklusive Betrag wird zusätzlich durch den Gesamtpunktestand begrenzt. Die im Profil gezeigten Bedingungen wurden am 10. November 2026 vom Nutzer bestätigt. Der tatsächliche Antrag unterliegt einer Prüfung durch MakerWorld.

Die USD-Anzeige schneidet nach zwei Nachkommastellen ab, entsprechend dem bereitgestellten Profil-Screenshot. Die Mindestschwelle wird mit dem ungekürzten Betrag geprüft. Fehlende Punkte werden auf drei Nachkommastellen aufgerundet. Diese Berechnung nimmt keine Auszahlung vor.

Für jeweils 7, 14 und 30 Tage gibt es drei weitere Sensoren. Sie zeigen verdiente Punkte, deren Gutschein-Gegenwert nach gewählter Punktebasis und den USD-Gegenwert exklusiver Einnahmen. Als Einnahmen gelten positive Punktebuchungen im Zeitfenster. Ausgaben werden nicht abgezogen. Der Zeitbezug ist der Buchungszeitpunkt aus dem Transaktionsverlauf. Ein Punkteverdienst für einen früheren Leistungstag wird deshalb dem späteren Buchungszeitpunkt zugerechnet.

Der rückwirkende Import nutzt denselben Bambu-Transaktions-Endpunkt wie die vorhandenen Gesamtsummen. Er liest Seiten mit bis zu 100 Buchungen, bis der 30-Tage-Zeitraum abgedeckt oder das Ende erreicht ist. Maximal 50 Seiten und zwei Minuten pro Import sind vorgesehen. Der Abruf erfolgt beim Laden und anschließend höchstens alle sechs Stunden. Die bestehenden Kontosensoren werden ungefähr alle 30 Minuten abgefragt. Gespeicherte Schutzpausen haben Vorrang.

Alle Historienseiten werden zuerst vollständig geprüft und danach gemeinsam übernommen. Bei einem Fehler stehen die neuen Zeitraumwerte auf nicht verfügbar. Die Attribute history_error und history_synced_at geben den bereinigten Fehler und den Zeitpunkt des letzten erfolgreichen Imports an. Der Zeitpunkt wird als Unix-Zeitstempel angegeben. Die minimalen Historienwerte mit Buchungszeit und Punktebeträgen werden lokal im Home-Assistant-Speicher zwischengespeichert. Ein Neustart übernimmt den Cache und den verbleibenden Sechs-Stunden-Abstand. Zugangsdaten und Modellnamen werden in diesem Cache nicht gespeichert.

Der Verlauf im angemeldeten Browser zeigte datierte Gutschriften einschließlich exklusiver Punkte. Der automatisierte Import mit dem Home-Assistant-Token muss noch live bestätigt werden. Bei abweichender Antwortstruktur erfolgt eine Fehlermeldung und keine Schätzung aus dem Kontostand. Insbesondere werden unbekannte Punkteaufteilungen nicht als Null ausgegeben.

Die neuen Sensoren eignen sich für Dashboard-Anzeigen und die normale Zustandshistorie. Für die abgeleiteten Sensoren werden keine Langzeitstatistiken eingerichtet. Ein Kurs- oder Punktebasiswechsel berechnet den angezeigten Gegenwert neu. Er beschreibt damit den Gegenwert zum aktuell eingestellten Kurs.


## Übersichtliche Sensorgruppen ab 0.4.0

Unter **Einstellungen → Geräte & Dienste → MakerWorld Creator Stats → Konfigurieren** zunächst eine Anzeige auswählen.

| Auswahl | Rechensensoren |
| --- | --- |
| Nur Guthaben-Gutscheine | Gutscheinwerte und deren 7-, 14- und 30-Tage-Gegenwerte |
| Nur direkte USD-Auszahlung | USD-Gegenwerte, Auszahlungsgrenzen und exklusive USD-Einnahmen für 7, 14 und 30 Tage |
| Gutscheine und USD-Auszahlung | Beide Gruppen |

Bestehende Installationen übernehmen beim Update zunächst beide Gruppen. Die Auswahl wird pro Konto gespeichert. Im USD-Modus ist keine Shopauswahl erforderlich. Vorhandene Gutschein-Einstellungen werden gespeichert und können bei einer späteren Umschaltung wieder genutzt werden.

Beim Speichern lädt Home Assistant die Integration neu. Abgewählte Rechengruppen werden aus der Entitätenliste entfernt und bei erneuter Auswahl wieder angelegt. Selbst angelegte Dashboard-Karten oder Automationen, die diese Entitäten verwenden, müssen zur Auswahl passen. Aktive Entitäten behalten ihre bisherigen eindeutigen Schlüssel. Die Konto- und Rohpunktesensoren werden weiter angeboten. Die drei allgemeinen Punkte-Einnahmensensoren verwenden im USD-Modus exklusive Punkte und sonst die gewählte Gutschein-Punktebasis.

### Bedeutung der Finanzwerte

| Bezeichnung | Bedeutung |
| --- | --- |
| Kontostand | Jetzt vorhandene Punkte nach bisherigen Ausgaben |
| Insgesamt verdient | Bisher gutgeschriebene Punkte, einschließlich später ausgegebener Punkte |
| Gutscheine – Kontowert anteilig | Aktueller Punktestand × Guthaben je Gutschein ÷ Punktekosten. Restpunkte werden anteilig bewertet |
| Gutscheine – Ganze Gutscheine finanzierbar | Ganze Anzahl der Gutscheine, abgerundet aus dem aktuellen Punktestand |
| Gutscheine – Guthaben ganzer Gutscheine | Ganze Gutscheinanzahl × Gutscheinwert |
| Gutscheine – Gesamtverdienst als Gegenwert | Bisher verdiente Punkte der gewählten Basis zum heute eingestellten Gutschein-Kurs |
| USD-Auszahlung – Aktueller Gegenwert | Vorhandene exklusive Punkte × 0,066 USD |
| USD-Auszahlung – Beantragbar rechnerisch | Durch Kontostand begrenzter exklusiver Betrag, ab 100 USD und maximal 1.000 USD pro Antrag |
| USD-Auszahlung – Gesamtverdienst als Gegenwert | Bisher verdiente exklusive Punkte × 0,066 USD |
| Einnahmen 7, 14 oder 30 Tage | Positive Buchungen im entsprechenden Zeitfenster. Ausgaben werden nicht abgezogen |

Beispielsweise ergeben 800 Punkte bei 40 EUR Guthaben für 524 Punkte einen anteiligen Kontowert von 61,07 EUR, einen ganzen Gutschein und 40 EUR Guthaben ganzer Gutscheine. Für den folgenden Gutschein fehlen 248 Punkte.

Die Erklärung jedes Rechensensors steht zusätzlich in seinem Attribut **beschreibung**. Geld-Gegenwerte und beantragbare Beträge beschreiben Rechenwerte. Tatsächliche Shopverfügbarkeit und die Prüfung eines Auszahlungsantrags erfolgen bei MakerWorld.
