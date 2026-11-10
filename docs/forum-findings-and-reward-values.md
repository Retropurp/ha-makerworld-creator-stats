# Forum-Erkenntnisse und regionale Gutscheinwerte

Auswertung am 10. November 2026 des Threads [Live stats app for Makerworld models analytics](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976). Alle 149 zum Abrufzeitpunkt öffentlich abrufbaren Beiträge wurden über die Themenliste und die nachgeladenen Beitrags-IDs erfasst. Die Beitragsnummerierung hat Lücken und endet bei 155. Verlinkte Medien und externe Unterseiten wurden nicht vollständig ausgewertet. Aussagen über die App stammen aus Berichten ihres Entwicklers und ihrer Nutzer.

## Nutzerwunsch für die nächste Erweiterung

Punkte in regionales Bambu-Shop-Guthaben umrechnen. Der Nutzer bezieht sich auf Guthaben-Gutscheine und möchte auch die weiteren im Forum genannten Währungen experimentell anbieten. Die konkreten regionalen Werte sollen ihren Quellenstand und einen sichtbaren experimentellen Hinweis erhalten. Die Implementierung ist noch offen.

Vorgeschlagene Sensoren sind der rechnerische Gegenwert des aktuellen Punktekontos und der bisher verdienten Punkte, die durch den Punktestand finanzierbare ganze Gutscheinanzahl, deren Guthaben, die fehlenden Punkte und der Fortschritt bis zum nächsten Gutschein. Dies beschreibt Rechenwerte anhand eines gewählten Angebots. Tatsächliche Einlösungen, Verfügbarkeit und freigegebene Punkte benötigen zusätzliche Nachweise.

## Historische regionale Vorlagen

Quelle [Beitrag 40 vom 10. April 2026](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/40), wiederholt in Beiträgen 62 und 66 im Mai. Die folgenden Werte sind Community-Angaben. Die aktuellen regionalen Punkteshop-Angebote wurden hier noch nicht bestätigt.

| Shopregion laut Forum | Währung | Guthaben | Punktekosten |
| --- | --- | --- | --- |
| USA | USD | 40 | 490 |
| EU | EUR | 40 | 524 |
| Vereinigtes Königreich | GBP | 35 | 535 |
| Kanada | CAD | 55 | 504 |
| Australien | AUD | 65 | 511 |
| Japan | JPY | 5300 | 502 |
| ASIA laut Forum, mit Singapur, Thailand, Malaysia, Hongkong/Macao/Taiwan | USD laut Dollarangabe im Kontext, noch bestätigen | 40 | 490 |
| Südkorea | KRW | 58000 | 490 |

Für China beschreibt derselbe Beitrag Youzan-Rabattangebote. Für ein Guthaben-Gutscheinprofil fehlt dort ein geeigneter Wert. Die China-Vorlage benötigt deshalb eine ausdrückliche Anzeige, dass in dieser Quelle kein passendes Guthaben-Angebot belegt ist. Rabattangebote nicht in den Guthaben-Rechner aufnehmen.

Auch die EU-Vorlage hat hier lediglich historischen Community-Nachweis, ergänzt um das vom Nutzer genannte Beispiel. Vorlagen mit Quellenlink, Datum und Verifizierungsstatus versehen. Alle Werte manuell überschreibbar machen. Region, ISO-Währung, Gutscheinwert und Punktekosten separat speichern. Rechenwerte bei fehlender oder ungültiger Konfiguration als nicht verfügbar behandeln. Währungen mit unterschiedlicher Zahl an Nachkommastellen in der Darstellung berücksichtigen. Decimal-Rechnung oder gleichwertige exakte Rechnung für Einlöseschwellen verwenden.

## Punktebasis und Auszahlung

[Beitrag 36](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/36) beschreibt einen Fehler durch die Annahme, reguläre Punkte würden stets für Gutscheine und exklusive stets für Barauszahlung genutzt. [Beiträge 88 und 89](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/88) melden später eine Auswahl zwischen regulären Punkten und regulären plus exklusiven Punkten für die Gutscheinrechnung.

Für unsere Konfiguration dieselbe Entscheidung explizit anbieten. Fachlich prüfen, ob alle herangezogenen Punkte tatsächlich zum Einlösen verfügbar sind. Den aktuellen Kontostand und den über die Zeit verdienten Gesamtbetrag getrennt berechnen. Den zum aktuellen Kurs umgerechneten Gesamtverdienst als rechnerischen Gegenwert beschriften. Für tatsächlich erhaltenes Gutschein-Guthaben wäre die Einlösehistorie nötig.

[Beiträge 62 bis 69](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/67) behandeln die unterschiedlichen regionalen Gutscheinwerte und die separat betrachtete Barauszahlung exklusiver Punkte in USD. Unser Gutscheinrechner braucht dafür einen eigenen Berechnungsmodus, falls später Barauszahlungen ergänzt werden. Wechselkurse, Gutscheinumrechnung und Barauszahlungsrate haben unterschiedliche Bedeutungen.

## Regionserkennung

In [Beitrag 62](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/62) und [Beitrag 66](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/66) berichtet der Entwickler, seine App übernehme nach Anmeldung die MakerWorld-Präferenzen der Shopregion. Der Thread nennt weder das genaue Feld noch den Endpunkt dafür.

Vor der Umsetzung die von unserer Anmeldung erreichbaren Profil- und gegebenenfalls Präferenzantworten untersuchen. Eine automatische Auswahl erst bei eindeutigem Feld-Mapping anbieten und weiterhin eine manuelle Korrektur ermöglichen. Sprache, Zeitzone und globale/chinesische API-Region reichen als Nachweis der Gutschein-Shopregion nicht aus.

## Geschichte und Tageswerte

Im April berichten [Beitrag 10](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/10) und [Beitrag 47](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/47) von lokal ab Installation gesammelten Zählerständen. Ab Juni und Juli melden [Beitrag 89](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/89) und [Beitrag 93](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/93) historische Creator-Center-Daten einschließlich Modell- und Druckprofilanalysen. Die frühere Aussage fehlender Historie beschreibt damit einen älteren Funktionsstand.

[Beitrag 16](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/16) berichtet von UTC-Tagesgrenzen und einer damaligen Punktegutschrift um 22 Uhr UTC für den vorherigen UTC-Tag. Vor einer Umsetzung heute erneut prüfen. Eigene Tagesdifferenzen anhand der Home-Assistant-Zeitzone eindeutig von Creator-Center-Tageswerten unterscheiden. Ein verspäteter Abruf darf die gesamte Änderung seit dem letzten Abruf nicht ungeprüft dem neuen Tag zuordnen. Sommerzeit, Neustarts und fehlende Tages-Basiswerte testen.

## Robustheit und Datenqualität

- [Beiträge 102 und 103](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/102) sowie [Beitrag 104](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/104) nennen unvollständige Antworten, große Modellkataloge, Null-Punktestände und ausgefallene Aktualisierungen als Fehlerquellen. Letzten erfolgreichen Wert mit Aktualitätsstatus verwalten. Fehlende Antworten und echte Nullwerte unterscheiden. Unsere derzeitigen Sensoren werden bei fehlenden Werten nicht verfügbar. Eine spätere Anzeige zwischengespeicherter Werte muss deren Alter erkennbar machen.
- [Beiträge 105 bis 112](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/105) berichten über Änderungen der Sicherheitsprüfung und Probleme mit Punkten in Benutzernamen nach einem Mehrkonten-Umbau. Stabile Konto-IDs nutzen und normale Sonderzeichen im Anzeigenamen testen. Die genaue Ursache des fremden Fehlers ist im Thread nicht technisch dokumentiert.
- [Beiträge 115 bis 123](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/115) dokumentieren einen MakerWorld-Ausfall und regional unterschiedliche Erholung. Temporäre Fehler nicht als Beweis eines gelöschten Kontos oder Modells behandeln.
- [Beitrag 101](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/101) beschreibt, dass Meilenstein-Benachrichtigungen erst vom aktuellen Stand bei Aktivierung zählen sollen. Für spätere Automationen eine Startbasis setzen.

## Abfragehäufigkeit und Anmeldung

[Beiträge 73 bis 77](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/73) behandeln Android-Hintergrundaktualisierung. Der dort genannte funktionierende Minutenabstand liefert keinen belastbaren Nachweis einer API-Abfragegrenze. [Beitrag 28](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/28) nennt fünf Minuten im Vordergrund und deutlich seltenere iOS-Hintergrundupdates. Für eine Intervalländerung unserer Integration bleiben eigene Fehlerbeobachtung und kontrollierte Rücknahme der Abfragehäufigkeit erforderlich.

[Beitrag 87](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/87) beschreibt eine Anmeldung über MakerWorld im integrierten Browser mit lokal gespeichertem Sitzungscookie. Das ist eine zusätzliche technische Möglichkeit, falls wir später Web-Analysedaten benötigen. Die Details und die Übertragbarkeit auf Home Assistant bleiben offen. Backups enthalten laut [Beitrag 89](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/89) in seiner App auch die Anmeldung. Für unsere Diagnoseexporte Zugangsdaten ausdrücklich auslassen.

## Weitere mögliche Erweiterungen

Spätere Ideen aus [Beitrag 93](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/93) und [Beitrag 104](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/104) sind Sparziele, Zeitverläufe, Druckprofil- und Provisionsanalysen. Sie sind bisher Rechercheansätze. Trending-Ranglisten hängen laut [Beiträgen 53 und 54](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/54) von Ansicht und Personalisierung ab. Ein möglicher Rang-Sensor braucht daher eine präzise benannte Rangliste.

## Hinweis auf ungeklärte Nutzungsbedingungen

In [Beitrag 137](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/137) und [Beitrag 140](https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/140) berichtet ein anderer Entwickler, Bambu habe die geplante API-Nutzung seiner Erweiterung auf Nachfrage abgelehnt. Der MakerStats-Entwickler bestätigt im Thread keine eigene Genehmigung. Dies ist ein Erfahrungsbericht über eine damalige Auskunft, kein Nachweis einer verbindlichen Bewertung unseres Projekts. Eine Darstellung als offiziell unterstützte Integration wäre durch diese Quellen nicht gedeckt.

## Priorität für die Wiederaufnahme

Zuerst den Gutscheinrechner mit den gewünschten experimentellen Regionalvorlagen, einer manuellen Anpassung und expliziter Punktebasis planen. Automatische Regionserkennung anhand tatsächlicher Daten prüfen. Den Rechenweg an Einlöseschwellen einschließlich Nachkommastellen testen. Danach die separat dokumentierte optionale Modellstatistik-Erweiterung aufgreifen. Weitere Forum-Funktionen bedürfen einer eigenen Festlegung des Umfangs.