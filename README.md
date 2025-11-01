# Schulsozialindex Karte

Eine Visualisierung der Schulen in NRW mit ihrem [Schulsozialindex](https://www.schulministerium.nrw/schulsozialindex) auf einer Karte

Dieses Projekt generiert mit Python eine [Webseite](https://homlador.github.io/schulsozialindex-karte/), auf der eine interaktive Karte unter Verwendung von [OpenStreetMap](https://www.openstreetmap.org) und [leaflet](https://leafletjs.com/) von Schulen und ihrem Schulsozialindex dargestellt wird.

Die Adressdaten basierend auf Daten von "IT.NRW, Statistisches Landesamt, Düsseldorf, 2025" unter der Datenlizenz Deutschland - Namensnennung - Version 2.0 

## HOWTO

0. `$ uv sync`

1. [Schul- und Adressverzeichnis](https://statistik.nrw/sites/default/files/2025-03/AS_BS_Verzeichnis_2024_25_%28gerundet%29_0.xlsx) von der Seite der [Schulkarte und Umkreissuche von Statistik.NRW](https://statistik.nrw/service/veroeffentlichungen/schulen-in-nordrhein-westfalen-und-ihre-erreichbarkeiten/schulkarte-und-umkreissuche)laden.
Manuell aufbereiten:
* Leere Zeilen und Zeilen mit Anmerkungen oben und unten löschen.
* Zeilenumbrüche und Fuoten aus Spaltenüberschriften entfernen. Insbesondere: Spalten B -> Schulform, E -> Schulnnummer, R -> Anzahl, 

2. [Schulsozialindex-Daten](https://www.schulministerium.nrw/system/files/media/document/file/schulliste_sj_25_26_open_data.csv) von der [Open Data Seite des Ministeriums für Schule und Bildung NRW](https://www.schulministerium.nrw/open-data) laden.

3. Schul- und Adressverzeichnis mit Sozialindex zusammenführen: `$ uv run merge_data.py`

3. Geokoordinaten mit [Nominatim](https://nominatim.org/) ergänzen: `$ uv run geocode_schools.py`

4. Daten nach JSON konvertieren: `$ uv run convert_to_json.py`
(Hier ggf. eine Auswahl treffen, um einen eigenen Datensatz zu erstellen)

5. Gradienten berechnen: `$ uv run analyze_gradients.py`

5. `index.html` öffnen

## TODO/Ideen

* Schulen ohne Sozialindex ausblenden
* Auswahl nach Bezirken o.ä dynamisch
* Gradienten per Javascript für ausgewählte Schulen berechnen und maximale Entfernung definierbar machen
* Schultyp PRIMUS-Schule ergänzen