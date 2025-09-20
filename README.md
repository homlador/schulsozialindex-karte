# Schulsozialindex Karte

Eine Visualisierung der Schulen in NRW mit ihrem [Schulsozialindex](https://www.schulministerium.nrw/schulsozialindex)  auf einer Karte

Dieses Projekt generiert mit Python eine Webseite, auf der eine interaktive Karte unter Verwendung von [OpenStreetMap](https://www.openstreetmap.org) und [leaflet](https://leafletjs.com/) von Schulen und ihrem Schulsozialindex dargestellt wird.
Die Adressdaten werden automatisiert mit [Nominatim](https://nominatim.org/) ergänzt, sind daher nicht vollständig und möglicherweise fehlerhaft.

## HOWTO

0. `$ uv sync`
1. [Daten aus PDF](https://www.schulministerium.nrw/system/files/media/document/file/sozialindex_schulliste_schuljahr_2025-26.pdf) extrahieren und in csv speichern: `$ uv run extract_data.py`
2. Ggf die ausgewählten Schulen in geocode_schools.py anpassen. 
Adressdaten ergänzen: `$ uv run geocode_schools.py`
Automatisiert werden die meisten Adressen (zumindest ungefährder weiterführenden Schulen gefunden. Fehlerquote unbekannt. Bei Grundschulen funktioniert es kaum.
ggf. Manuell ergänzen bzw korrigieren
3. Daten nach JSON konvertieren: `$ uv run convert_to_json`
3. index.html öffnen
