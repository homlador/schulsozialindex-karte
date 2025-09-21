"""
Sucht zu Schulen in NRW die Geokoordinaten (Latitude, Longitude) mittels Nominatim (OpenStreetMap)
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pandas as pd
import time
import os

def load_existing_coordinates():
    if os.path.exists('schulen-mit-koordinaten.csv'):
        existing_df = pd.read_csv('schulen-mit-koordinaten.csv')
        # Erstelle ein Dictionary mit Schulnummer als Schlüssel
        return existing_df.set_index('Schulnummer')[['latitude', 'longitude', 'found_address']].to_dict('index')
    return {}

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
        city = school_info['Ort']
        school_name = school_info['Amtliche Bezeichnung 1']
        school_type = school_info['Schulform']            
        school_name = school_name.replace('Städt.', '')
        school_adress = school_info['Straße und Hausnummer']
        
        # Baue verschiedene Queries für bessere Trefferchancen
        queries = [                 
            f"{school_name} {school_adress} {city}",                                      
            f"{school_adress} {city}",    
            f"{school_name} {city}",                        
            f"{school_name} {school_type} {city}"
        ]
        
        # Versuche alle Queries
        for query in queries:
            print(f"  Versuche: {query}")
            location = do_geocode(geolocator, query)
            if location:
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'found_address': location.address,
                    'used_query': query
                }
            # Warte 1 Sekunde zwischen Anfragen (Nominatim Policy)
            time.sleep(1)        
        return None
    except Exception as e:
        print(f"Fehler bei {school_name}: {str(e)}")
        return None

def main():       
    # Definiere die Datentypen für die Spalten, damit diese nicht als float mit XYZ.0 gespeichert werden
    columns_with_int = ['Amtlicher Gemeindeschlüssel', 'Schulformschlüssel', 'Schulnummer', 'Sozialindex', 'Anzahl', 'Postleitzahl', 'Amtlicher Gemeinde-schlüssel']    
    types = {col: 'Int32' for col in columns_with_int}
    df = pd.read_csv('AS_BS_Verzeichnis_2024_25_mit_Sozialindex.csv', dtype=types)       
    print(f"{len(df)} Schulen aus CSV gelesen.")
    
    # ----------------------- Ab hier anpassen zum Filtern ----------------------- 
    # Filtere nur eine Auswahl an Städten
    auswahl_staedte = None    
    #auswahl_staedte = ['Duisburg']        
    if auswahl_staedte is not None:
        df_schulen = df[df['Ort'].isin(auswahl_staedte)].copy()
    else:
        df_schulen = df.copy()
    
    # Den Schulsozialindex gibt es nicht für Berufskollegs und Förderschulen                
    schulformen = [
        'Grundschule', 
        'Gesamtschule', 
        'Gymnasium', 
        'Realschule', 
        'Hauptschule', 
        'Sekundarschule'
    ]
    df_schulen = df_schulen[df_schulen['Schulform'].isin(schulformen)]
    #df_schulen = df_schulen[df_schulen['Verwaltungsbezirk'].isin(['Düsseldorf'])]
    
    # ----------------------- Ende Anpassungen -----------------------
    
    print(f"{len(df_schulen)} Schulen in Auswahl.")
    
    # Lade vorhandene Koordinaten
    existing_coordinates = load_existing_coordinates()
    
    print(f"{len(existing_coordinates)} Existierende Koordinaten geladen.")
    
    # Neue Spalten für die Koordinaten, falls sie noch nicht existieren
    if 'latitude' not in df_schulen.columns:
        df_schulen['latitude'] = None
    if 'longitude' not in df_schulen.columns:
        df_schulen['longitude'] = None
    if 'found_address' not in df_schulen.columns:
        df_schulen['found_address'] = None
    
    # Initialisiere Geocoder
    geolocator = Nominatim(user_agent="schulsozialindex_geocoder")
    
    # Durchlaufe alle Schulen
    for idx, row in df_schulen.iterrows():
        row['Schulnummer'] = pd.to_numeric(row['Schulnummer'], downcast='integer', errors='coerce')
        school_number = row['Schulnummer']
        school_name = row['Amtliche Bezeichnung 1'].strip('"')
        
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
        
        print(f"\nSuche neue Koordinaten für: {school_name}")
        result = None
        result = geocode_school(geolocator, row)
        
        if result:
            df_schulen.at[idx, 'latitude'] = result['latitude']
            df_schulen.at[idx, 'longitude'] = result['longitude']
            df_schulen.at[idx, 'found_address'] = result['found_address']
            print(f"Gefunden: {result['latitude']}, {result['longitude']}")
            print(f"Adresse: {result['found_address']}")
        else:
            print(f"Keine Koordinaten gefunden für {school_name}")    
    
    # Speichere Ergebnisse
    output_file = 'schulen-mit-koordinaten.csv'
    df_schulen.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nErgebnisse wurden in '{output_file}' gespeichert.")
    
    # Statistiken
    found = df_schulen['latitude'].notna().sum()
    total = len(df_schulen)
    print(f"\nStatistik:")
    print(f"Gefunden: {found} von {total} ({found/total*100:.1f}%)")
    
    if found < total:
        print("\nNicht gefundene Schulen:")
        not_found = df_schulen[df_schulen['latitude'].isna()]
        for _, row in not_found.iterrows():
            print(f"- {row['Amtliche Bezeichnung 1']}")

if __name__ == "__main__":
    main()
