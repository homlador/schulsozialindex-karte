"""
Sucht zu Schulen in NRW die Geokoordinaten (Latitude, Longitude) mittels Nominatim (OpenStreetMap)
Ein erster Durchlauf dauert ca 2 Stunden, da zwischen den Anfragen 1 Sekunde gewartet wird (Nominatim Policy).
Wenn nicht alle Schulen gefunden wurden, kann das Script erneut ausgeführt werden, da bereits gefundene Koordinaten ergänzt werden.
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pandas as pd
import time
import os

def load_existing_coordinates():
    if os.path.exists('AS_BS_Verzeichnis_2024_25_mit_Sozialindex_und_Koordinaten.csv'):
        existing_df = pd.read_csv('AS_BS_Verzeichnis_2024_25_mit_Sozialindex_und_Koordinaten.csv', dtype=str)

        # Zeilen entfernen, bei denen keine Schulnummer vorhanden ist
        existing_df = existing_df[existing_df['Schulnummer'].notna()]
    
        # Erstelle ein Dictionary mit Schulnummer als Schlüssel und gib die Anzahl der vorhandenen Koordinaten zurück        
        return existing_df['latitude'].notna().sum(), existing_df.set_index('Schulnummer')[['latitude', 'longitude', 'found_address']].to_dict('index')
    return 0, {}

def do_geocode(geolocator, query, attempt=1, max_attempts=5):
    try:
        return geolocator.geocode(query, exactly_one=True)
    except GeocoderTimedOut:
        if attempt <= max_attempts:
            return do_geocode(geolocator, query, attempt=attempt+1)
        raise
    
def geocode_school(geolocator, school_info):
    try:
        # Extrahiere Stadt und Schulname
        school_name = school_info['Amtliche Bezeichnung 1']
        query = school_info['Straße und Hausnummer'] + ', ' + school_info['Postleitzahl']
        print(f"Suche nach Adresse: {query}")
        location = do_geocode(geolocator, query)

        if location:
            return {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'found_address': location.address,
            }
        else:
            return None
    except Exception as e:
        print(f"Fehler bei {school_name}: {str(e)}")
        return None

def main():       
    # Definiere die Datentypen für die Spalten, damit diese nicht als float mit XYZ.0 gespeichert werden
    df_schulen = pd.read_csv('AS_BS_Verzeichnis_2024_25_mit_Sozialindex.csv', dtype=str)       
    print(f"{len(df_schulen)} Schulen aus CSV gelesen.")
    
    # Lade vorhandene Koordinaten
    count_existing_coordinates, existing_coordinates = load_existing_coordinates()
    print(f"{count_existing_coordinates} Schulen mit Koordinaten.")
    to_find = len(df_schulen) - count_existing_coordinates
    print(f"{to_find} Schulen ohne Koordinaten.")

    # Neue Spalten für die Koordinaten, falls sie noch nicht existieren
    if 'latitude' not in df_schulen.columns:
        df_schulen['latitude'] = None
    if 'longitude' not in df_schulen.columns:
        df_schulen['longitude'] = None
    if 'found_address' not in df_schulen.columns:
        df_schulen['found_address'] = None
    
    # Initialisiere Geocoder
    geolocator = Nominatim(user_agent="schulsozialindex_geocoder", timeout=20)
    no = 1
    # Durchlaufe alle Schulen
    for idx, row in df_schulen.iterrows():
        school_number = row['Schulnummer']
        school_name = row['Amtliche Bezeichnung 1']
               
        # Prüfe ob bereits Koordinaten existieren
        if school_number in existing_coordinates:
            existing = existing_coordinates[school_number]
            if pd.notna(existing['latitude']) and pd.notna(existing['longitude']):
                #print(f"\nVerwende vorhandene Koordinaten für: {school_name})")
                df_schulen.at[idx, 'latitude'] = existing['latitude']
                df_schulen.at[idx, 'longitude'] = existing['longitude']
                df_schulen.at[idx, 'found_address'] = existing['found_address']
                #print(f"Koordinaten: {existing['latitude']}, {existing['longitude']}")
                continue
        
        print(f"\nSuche neue Koordinaten für: {school_name} ({school_number}) [{no}/{to_find}]")
        
        result = geocode_school(geolocator, row)
        
        if result:
            df_schulen.at[idx, 'latitude'] = result['latitude']
            df_schulen.at[idx, 'longitude'] = result['longitude']
            df_schulen.at[idx, 'found_address'] = result['found_address']
            print(f"Gefunden: {result['latitude']}, {result['longitude']}")
            print(f"Adresse: {result['found_address']}")
        else:
            print(f"Keine Koordinaten gefunden für {school_name}")    
        no += 1
        
    # Speichere Ergebnisse
    output_file = 'AS_BS_Verzeichnis_2024_25_mit_Sozialindex_und_Koordinaten.csv'
    df_schulen.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nErgebnisse wurden in '{output_file}' gespeichert.")
    
    # Statistiken
    found = df_schulen['latitude'].notna().sum()
    total = len(df_schulen)
    print(f"\nStatistik:")
    print(f"Gefunden: {found} von {total} ({found/total*100:.1f}%)")
        
    if found < total:
        print(f"\nNicht gefundene Schulen: {total - found}")
        not_found = df_schulen[df_schulen['latitude'].isna()]
        for _, row in not_found.iterrows():
            print(f"- {row['Amtliche Bezeichnung 1']} ({row['Schulnummer']})")

if __name__ == "__main__":    
    start_time = time.time()
    main()
    end_time = time.time()
    laufzeit = int(end_time - start_time)
    stunden, rest = divmod(laufzeit, 3600)
    minuten, sekunden = divmod(rest, 60)
    print(f"\nLaufzeit: {stunden:02d}h:{minuten:02d}m:{sekunden:02d}s")
