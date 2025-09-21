# Schulsozialindex Karte

Eine Visualisierung der Schulen in NRW mit ihrem [Schulsozialindex](https://www.schulministerium.nrw/schulsozialindex)  auf einer Karte

Dieses Projekt generiert mit Python eine [Webseite](https://homlador.github.io/schulsozialindex-karte/), auf der eine interaktive Karte unter Verwendung von [OpenStreetMap](https://www.openstreetmap.org) und [leaflet](https://leafletjs.com/) von Schulen und ihrem Schulsozialindex dargestellt wird.

Die Adressdaten basierend auf Daten von "IT.NRW, Statistisches Landesamt, Düsseldorf, 2025"  unter der Datenlizenz Deutschland - Namensnennung - Version 2.0 

## HOWTO

0. `$ uv sync`

1. [Daten vom Schulsozialindex aus PDF](https://www.schulministerium.nrw/system/files/media/document/file/sozialindex_schulliste_schuljahr_2025-26.pdf) extrahieren und in csv speichern: `$ uv run extract_data.py`

2. [Schul- und Adressverzeichnis](https://statistik.nrw/sites/default/files/2025-03/AS_BS_Verzeichnis_2024_25_%28gerundet%29_0.xlsx) laden.
Manuell aufbereiten
* Leere Zeilen und Zeilen mit Anmerkungen oben und unten löschen.
* Spalten umbenennen zu: Schulnnummer, Anzahl, Verwaltungsbezirk.

3. Geokoordinaten mit [Nominatim](https://nominatim.org/) ergänzen: `$ uv run geocode_schools.py`
(Ggf die ausgewählten Schulen in geocode_schools.py anpassen)

4. Daten nach JSON konvertieren: `$ uv run convert_to_json.py`

5. `index.html` öffnen

## TODO

* Darstellung der Schulen als Kreis mit Grösse abhängig von der Schülerzahl
* Auswahl nach Bezirken o.ä per Javascript