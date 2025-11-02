# Schulsozialindex Karte

Eine Visualisierung der Schulen in NRW mit ihrem [Schulsozialindex](https://www.schulministerium.nrw/schulsozialindex) auf einer Karte.

Dieses Projekt generiert mit Python eine [Webseite](https://homlador.github.io/schulsozialindex-karte/), auf der eine interaktive Karte unter Verwendung von [OpenStreetMap](https://www.openstreetmap.org) und [leaflet](https://leafletjs.com/) von Schulen und ihrem Schulsozialindex dargestellt wird.

## HOWTO

0. `$ uv sync`

Die Schritte 1 bis 4 sind nur nötig, wenn sich die Datengrundlage ändert.

1. [Schul- und Adressverzeichnis](https://statistik.nrw/sites/default/files/2025-03/AS_BS_Verzeichnis_2024_25_%28gerundet%29_0.xlsx) von der Seite der [Schulkarte und Umkreissuche von Statistik.NRW](https://statistik.nrw/service/veroeffentlichungen/schulen-in-nordrhein-westfalen-und-ihre-erreichbarkeiten/schulkarte-und-umkreissuche) laden.
Manuell aufbereiten:
* Leere Zeilen und Zeilen mit Anmerkungen oben und unten löschen.
* Zeilenumbrüche und Fuoten aus Spaltenüberschriften entfernen. Insbesondere: Spalten B -> Schulform, E -> Schulnnummer, R -> Anzahl, 

2. [Schulsozialindex-Daten](https://www.schulministerium.nrw/system/files/media/document/file/schulliste_sj_25_26_open_data.csv) von der [Open Data Seite des Ministeriums für Schule und Bildung NRW](https://www.schulministerium.nrw/open-data) laden.

3. Schul- und Adressverzeichnis mit Sozialindex zusammenführen: `$ uv run merge_data.py`

4. Geokoordinaten mit [Nominatim](https://nominatim.org/) ergänzen: `$ uv run geocode_schools.py`

Die kombinierten Daten der Schulen inkl. Geokoordinaten liegen in der Datei `AS_BS_Verzeichnis_2024_25_mit_Sozialindex_und_Koordinaten.csv`. Daraus werden die JSON-Daten unter `docs/` erzeugt. Per Default werden alle Schulen in `docs/schools.json` gespeichert. Um einen eigenen Datensatz (z.B. eine Auswahl von bestimmten Schulen) zu erstellen, muss der Code in `convert_to_json.py` modifizert werden und diese Datei dann in der `index.html` unter `datasetSelect` hinzugefügt werden.

5. Daten nach JSON konvertieren: `$ uv run convert_to_json.py`

6. Gradienten berechnen: `$ uv run analyze_gradients.py`

7. `index.html` öffnen

## Datengrundlage und Lizenzen

Die [Adressdaten der Schulen](https://statistik.nrw/sites/default/files/2025-03/AS_BS_Verzeichnis_2024_25_%28gerundet%29_0.xlsx) sind von "IT.NRW, Statistisches Landesamt, Düsseldorf, 2025" unter der [Datenlizenz Deutschland - Namensnennung - Version 2.0.](https://www.govdata.de/dl-de/by-2-0)

Die [Daten des Schulsozialindex](https://www.schulministerium.nrw/system/files/media/document/file/schulliste_sj_25_26_open_data.csv) sind von "Ministerium für Schule und Bildung NRW" unter der [Datenlizenz Deutschland - Namensnennung - Version 2.0.](https://www.govdata.de/dl-de/by-2-0)

## TODO/Ideen

* Auswahl nach Bezirken o.ä dynamisch
* Gradienten per Javascript für ausgewählte Schulen berechnen und maximale Entfernung definierbar machen