# Modellstatistiken für eine spätere Version

Stand 10. November 2026. Entwicklungsnotiz für MakerWorld Creator Stats.

## Auftrag und Entscheidungsstand

Der Nutzer möchte die Untersuchung der Modellstatistiken und die Überlegungen zur Belastung von Home Assistant für eine spätere Version festhalten. Die Umsetzung soll später anhand dieser Notiz wieder aufgenommen werden. Eine konkrete Zielversion und der endgültige Funktionsumfang sind noch offen.

Die bestehende Integration bietet 25 Kontosensoren. Eine zusätzliche Auswahl von Modellen und Kennzahlen wurde vorgeschlagen, weil sechs Sensoren für jedes der zuletzt angezeigten 49 Modelle bereits 294 zusätzliche Sensoren ergeben würden. Der Nutzer hat noch keine konkrete Modellauswahl, Kennzahlenauswahl oder Aktualisierungsfrequenz festgelegt. Das Beispiel mit zehn Modellen und drei Kennzahlen beschreibt eine mögliche Konfiguration.

## Bestehender Projektstand

- Repository [Retropurp/ha-makerworld-creator-stats](https://github.com/Retropurp/ha-makerworld-creator-stats).
- Integrationsdomain `makerworld_creator_stats`.
- Release `0.1.2` ist der in diesem Chat zuletzt veröffentlichte Stand.
- Anmeldung mit Bambu-E-Mail-Adresse und Einmalcode. Home Assistant speichert den Zugangstoken lokal.
- Drei Statistikabfragen pro erfolgreichem Durchlauf liefern Profilwerte, Punktebewegungen und Boost-Token-Werte.
- Das reguläre Abfrageintervall beträgt 15 Minuten relativ zum Laden der Integration. Nach Fehlern der Profilabfrage beträgt es zwei Stunden.
- Version `0.1.1` behandelt leere Erfolgsantworten beim Anfordern des Codes und zeigt genauere, bereinigte Fehlermeldungen.
- Version `0.1.2` erhält Punktewerte mit Nachkommastellen. Zuvor wurden solche Werte verworfen und exklusive Punkte teilweise als nicht verfügbar angezeigt.
- Der Nutzer hat per Screenshot bestätigt, dass die zuvor fehlenden exklusiven Punktewerte mit Nachkommastellen erscheinen. 22 lokale Tests bestanden bei der letzten Codeänderung. Der Screenshot bestätigt diesen konkreten Live-Fall.

## Untersuchte Referenz

[dreed47/omarchy-makerworld](https://github.com/dreed47/omarchy-makerworld), heruntergeladene Fassung mit Versionsangabe `0.3.0`, untersucht am 10. November 2026. Das Projekt ist ein Linux-Desktop-Plugin mit QML, Quickshell, JavaScript und Python-Hilfsprogrammen. Die 55 JavaScript-Tests wurden lokal erfolgreich ausgeführt. Die QML-Oberfläche wurde hier nicht gestartet. Aussagen in dieser Notiz beziehen sich auf die damals gelesene Fassung. Vor einer Übernahme den aktuellen Quellstand erneut prüfen und den verwendeten Commit festhalten.

Wichtige Dateien sind `Model.js` für Endpunkte und Parser, `Panel.qml` für die Modellliste, `Service.qml` für regelmäßige Abfragen sowie `bin/makerworld-refresh` für die Token-Erneuerung.

## Datenquelle für Modelle

Die Referenz verwendet den zusätzlichen Endpunkt auf demselben Bambu-API-Host.

```http
GET https://api.bambulab.com/v1/design-service/my/design/published?limit=60&offset=0
Authorization: Bearer <vorhandener Zugangstoken>
```

Der vorhandene Token unserer Integration könnte hierfür ausreichen. Die Modellabfrage mit unserem Anmeldeverfahren wurde noch nicht live bestätigt. Die Referenz erwartet eine Antwort mit `total` und einer Liste `hits`. Ihr Parser akzeptiert zusätzlich bestimmte abweichende Verpackungen wie `data` und `list`.

| Information | Antwortfeld |
| --- | --- |
| Stabile Modell-ID | `id` |
| Titel | `title`, ersatzweise `titleTranslated` |
| Downloads | `downloadCount` |
| Likes | `likeCount` |
| Drucke | `printCount` |
| Sammlungen | `collectionCount` |
| Kommentare | `commentCount` |
| Boosts | `boostCnt` |
| Vorschaubild | `coverUrl` |
| Linkbestandteil | `slug` |

Die Referenz verarbeitet sechs Zähler pro Modell. Ihre Oberfläche zeigt Downloads, Likes, Drucke und gegebenenfalls Kommentare an. Sie bietet eine Sortierung nach Downloads, Likes und Drucken.

Modell-Downloads, Druckprofil-Downloads und die unterschiedlichen Kontosummen müssen fachlich sauber beschriftet und anhand echter Antworten abgeglichen werden. Eine Gleichheit der Summe aller Modellzähler mit einer bestimmten Profilzahl ist noch zu prüfen.

## Grenzen und Unterschiede der Referenz

1. `Panel.qml` ruft die Modellliste fest mit `limit=60&offset=0` ab. Eine Schleife für weitere Seiten fehlt im untersuchten Code. Für unsere Umsetzung alle Seiten berücksichtigen und das tatsächliche Verhalten von `limit`, `offset` und `total` prüfen.
2. Nach erfolgreichem Laden setzt die Oberfläche `designsLoaded=true`. Weitere Aktualisierungen rufen die Modellliste nur auf, solange dieser Wert falsch ist. Die Modellwerte erhalten innerhalb derselben geladenen Oberfläche dadurch keine regelmäßige Aktualisierung.
3. Der Parser wandelt fehlende oder ungültige Modellzähler mit `parseInt(...) || 0` in Null um. Unsere Sensoren sollen zwischen einer echten Null und einem fehlenden Wert unterscheiden.
4. Die regelmäßige Nachrichtenabfrage läuft standardmäßig alle fünf Minuten, mindestens alle zwei Minuten. Profilwerte laufen standardmäßig alle 15 Minuten, mindestens alle fünf Minuten. Ein geöffnetes Fenster löst zusätzliche Abfragen aus. Diese Zeiten belegen keine von Bambu zugesicherte Belastungsgrenze.
5. Die Referenz unterstützt außerdem Nachrichten, Kommentare, Benachrichtigungen, Gelesen-Markierungen und automatische Token-Erneuerung bei vorhandenem Refresh-Token. Diese Funktionen wurden besprochen, ihr Einbau gehört bisher zu keiner festgelegten späteren Version.

## Vorgeschlagene Home-Assistant-Umsetzung

- Die Integration um eine optionale Modellabfrage ergänzen.
- Eine Auswahl der gewünschten Modelle anhand stabiler IDs und eine Auswahl der Kennzahlen anbieten. Titeländerungen sollen bestehende Sensoren erhalten.
- Als mögliche Darstellung pro ausgewähltem Modell ein Gerät mit den gewählten Zahlensensoren sowie Modellname und Modelllink prüfen.
- Modellseiten gemeinsam abrufen und daraus die Sensoren versorgen. Die Zahl der Sensoren soll keine einzelne HTTP-Anfrage je Sensor auslösen.
- Den zusätzlichen Endpunkt eng in die bestehende Freigabe erlaubter Ziele und Methoden aufnehmen.
- Fehlende Werte als nicht verfügbar behandeln. Teilfehler oder unvollständige Seiten dürfen keine falschen Nullwerte und keine voreilige Löschung von Modellen verursachen.
- Verhalten bei neuen, umbenannten, gelöschten oder auf privat gesetzten Modellen vor der Umsetzung festlegen.
- Die Konfiguration vorhandener Installationen ohne neue Anmeldung übernehmen, soweit der vorhandene Token die Modellabfrage erlaubt.
- Einen gesonderten, konfigurierbaren Modell-Abstand erwägen. Der endgültige Standard und die erlaubten Grenzen sind offen.

## Belastung von Home Assistant

Bei 49 Modellen und sechs Kennzahlen entstehen bis zu 294 zusätzliche Zahlensensoren. Bei 15 Minuten Intervall ergeben sich rechnerisch 28.224 betrachtete Sensorwerte pro Tag. Daraus folgt weder dieselbe Zahl an HTTP-Anfragen noch dieselbe Zahl an Datenbankeinträgen.

Die tatsächliche Last hängt von Seitengrößen, Änderungen der Werte, Sensorattributen, Recorder-Konfiguration, Statistikklassen und der Hardware ab. Eine konkrete Speicher- oder CPU-Angabe wurde noch nicht gemessen. Die Hardware des Nutzers ist unbekannt.

Für eine spätere Messung Speicherbedarf, Laufzeit der Abfrage und Datenbankwachstum bei gleicher Konfiguration vor und nach Aktivierung der Modellsensoren vergleichen. Geeignete Statistikklassen bewusst wählen, da Modellzähler bei Löschung oder Korrektur sinken können. Zehn Modelle mit drei Kennzahlen wären beispielsweise 30 Sensoren und könnten für einen ersten Test genügen.

## Prüfung vor Veröffentlichung

- Bestehende Kontosensoren, Einmalcode-Anmeldung und erneute Anmeldung weiter prüfen.
- Modellantwort mit dem bestehenden Token direkt in Home Assistant testen und Werte gegen MakerWorld vergleichen.
- Mehr als 60 Modelle, mehrere Seiten, leere Liste, doppelte IDs und inkonsistente Seitensummen behandeln.
- Echte Nullwerte, fehlende Zähler, ungültige Typen und Änderungen des Antwortformats testen.
- Stabile Entitäts-IDs bei Titeländerungen, Konfigurationswechseln, Neustart und Update prüfen.
- Unvollständige Abfragen, Zeitüberschreitung, HTTP 401, HTTP 403 und HTTP 429 berücksichtigen. Wiederholungen und Wartezeiten auf API-Fehler abstimmen.
- Zugangsdaten und Tokens aus Protokollen und öffentlichen Fehlerberichten fernhalten. Das Nachladen von Vorschaubildern gegebenenfalls gesondert prüfen.
- Release Notes, Anleitung und Lizenzhinweise entsprechend der tatsächlich umgesetzten Fassung aktualisieren.

## Wiederaufnahme

Bei einer späteren Bitte um Modellstatistiken zuerst diese Notiz und den aktuellen Repository-Stand lesen. Dann die noch offenen Entscheidungen zur Modellauswahl, den Kennzahlen und dem Abfrageintervall auflösen. Die Modell-Schnittstelle anhand einer echten Antwort bestätigen, die Erweiterung implementieren und erst nach passenden Tests als neue Version veröffentlichen.

Die Referenz steht unter [MIT-Lizenz](https://github.com/dreed47/omarchy-makerworld/blob/master/LICENSE). Bei Übernahme von Code dessen Copyright- und Lizenzhinweise beibehalten und die Herkunft dokumentieren.