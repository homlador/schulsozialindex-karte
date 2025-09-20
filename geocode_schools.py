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

def geocode_school(geolocator, school_info):
    try:
        # Extrahiere Stadt und Schulname
        city = school_info['Kreis/Stadt']
        school_name = school_info['Schulname']
        school_type = school_info['Schulform']
        
        # Entferne Anführungszeichen und Stadt-Präfix
        school_name = school_name.strip('"')
        if ", " in school_name:
            city, school_name = school_name.split(", ", 1)
        
        # Extrahiere den eigentlichen Schulnamen und entferne Präfixe
        name_parts = school_name.split()
        if len(name_parts) > 1 and name_parts[0].upper() in ['GG', 'RS', 'GE', 'GH', 'SK', 'GYM', 'KG']:
            school_name = " ".join(name_parts[1:])
        
        # Normalisiere Schultyp
        school_type_map = {
            'GG': 'Gemeinschaftsgrundschule',
            'KG': 'Katholische Grundschule',
            'EG': 'Evangelische Grundschule',
            'GE': 'Gesamtschule',
            'Gym': 'Gymnasium',
            'RS': 'Realschule',
            'GH': 'Hauptschule',
            'SK': 'Sekundarschule'
        }
        
        if school_type in school_type_map:
            school_type = school_type_map[school_type]
        
        # Entferne das Wort "Stadt" aus dem Stadtnamen
        city = city.replace("Stadt ", "").strip()
        city = city.replace("Kreis ", "").strip()
                    
        school_name = school_name.replace('Gym ', '')
        school_name = school_name.replace('GE', '')
        school_name = school_name.replace('Schule', '')
        school_name = school_name.replace('Gesamtsch.', '')
        
        # Baue verschiedene Queries für bessere Trefferchancen
        queries = [                        
            f"{school_name} {school_type} {city}",
            f"{school_name} {city}",            
            f"{school_name} Schule {city}",            
            f"{school_type} {city}",
        ]
        
        # Versuche alle Queries
        for query in queries:
            print(f"  Versuche: {query}")
            location = geolocator.geocode(f"{query}, Deutschland", exactly_one=True)
            if location:
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'found_address': location.address,
                    'used_query': query
                }
            
        location = geolocator.geocode(query, exactly_one=True)
        
        if location:
            return {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'found_address': location.address
            }
        return None
    except Exception as e:
        print(f"Fehler bei {school_name}: {str(e)}")
        return None

def main():       
    df = pd.read_csv('alle_schulen.csv')        
    print(f"{len(df)} Schulen aus CSV gelesen.")
    
    # ----------------------- Ab hier anpassen zum Filtern ----------------------- 
    # Filtere nur eine Auswahl an Städten
    auswahl_staedte = None
    auswahl_schulnummern = None
    # Beispielhafte Auswahl
    #auswahl_staedte = ['Stadt Duisburg']    
    #auswahl_schulnummern = [164306, 164549, 164586, 164598, 164604, 164616, 164641, 164665, 164677, 164847, 165116, 165517, 165979, 165992, 166005, 166017, 166030, 166080, 183532, 185267, 187793, 188177, 188499, 188712, 189261, 189583, 189595, 191395, 191474, 192211, 193252]     
    if auswahl_staedte is not None:
        df_schulen = df[df['Kreis/Stadt'].isin(auswahl_staedte)].copy()
    elif auswahl_schulnummern is not None:
        df_schulen = df[df['Schulnummer'].isin(auswahl_schulnummern)].copy()
    else:
        df_schulen = df.copy()
                    
    schulformen = [
        'Grundschule', 
        'Gesamtschule', 
        'Gymnasium', 
        'Realschule', 
        'Hauptschule', 
        'Sekundarschule'
    ]
    #df_schulen = df_schulen[df_schulen['Schulform'].isin(schulformen)]
    #df_schulen = df_schulen[df_schulen['Bezirksregierung'].isin(['Düsseldorf'])]
    
    # ----------------------- Ende Anpassungen -----------------------
    
    print(f"{len(df_schulen)} Schulen in Auswahl.")
    
    # Lade vorhandene Koordinaten
    existing_coordinates = load_existing_coordinates()
    
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
        school_number = row['Schulnummer']
        school_name = row['Schulname'].strip('"')
        
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
        result = geocode_school(geolocator, row)
        
        if result:
            df_schulen.at[idx, 'latitude'] = result['latitude']
            df_schulen.at[idx, 'longitude'] = result['longitude']
            df_schulen.at[idx, 'found_address'] = result['found_address']
            print(f"Gefunden: {result['latitude']}, {result['longitude']}")
            print(f"Adresse: {result['found_address']}")
        else:
            print(f"Keine Koordinaten gefunden für {school_name}")
        
        # Warte 1 Sekunde zwischen Anfragen (Nominatim Policy)
        time.sleep(1)
    
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
            print(f"- {row['Schulname']}")

if __name__ == "__main__":
    main()
