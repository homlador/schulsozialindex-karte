import pandas as pd
import json
import time
import gzip
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Berechnet die Haversine-Distanz zwischen zwei Punkten auf der Erde.
    Gibt die Entfernung in Kilometern zurück.
    """
    R = 6371  # Erdradius in Kilometern

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

def prepare_dataframe(df):
    df = df.copy()
        
    df['lat'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['lon'] = pd.to_numeric(df['longitude'], errors='coerce')

    # Schulen ohne Koordinaten entfernen
    missing_schools = df[df['lat'].isnull() | df['lon'].isnull()]['schulnummer'].tolist()
    if missing_schools:
        print(f"Schulen ohne Koordinaten (werden entfernt): {missing_schools}")
    df = df[df['lat'].notnull() & df['lon'].notnull()]
    
    df['sozialindex'] = pd.to_numeric(df['sozialindex'], errors='coerce')
    df = df.reset_index(drop=True)
    return df

def analyze_schools(df):        
    results = []
    for i, school1 in df.iterrows():    
        for j, school2 in df.iloc[i+1:].iterrows():  
            # Status ausgabe alle 1000 Iterationen
            if (i * len(df) + j) % 100000 == 0:
                print(f"Analysiere Schule {i+1}/{len(df)} mit Schule {j+1}/{len(df)}")              
                
            distance = haversine_distance(
                float(school1['lat']), float(school1['lon']),
                float(school2['lat']), float(school2['lon'])
            )
            
            # Minimale Entfernung von 0 km und maximale Entfernung von 5 km
            if distance > 5:
                continue     
            if distance == 0:
                #print (f"Entfernung zwischen Schule {school1['schulnummer']} und {school2['schulnummer']} ist 0 km. Verwende 0.05 km.")
                distance = 0.05  # Vermeide Division durch Null            
            
            # Mindestdifferenz von 3 Stufen
            index_diff = abs(school1['sozialindex'] - school2['sozialindex'])       
            if index_diff >= 3:  
                gradient = index_diff / distance
                results.append({
                    'schule_1': {
                        'schulnummer': school1['schulnummer'],
                        'schultyp': school1['schultyp'],
                        'sozialindex': int(school1['sozialindex']),
                        'lat': school1['lat'],
                        'lon': school1['lon']
                    },
                    'schule_2': {
                        'schulnummer': school2['schulnummer'],
                        'schultyp': school2['schultyp'],
                        'sozialindex': int(school2['sozialindex']),
                        'lat': school2['lat'],
                        'lon': school2['lon']
                    },
                    'differenz': int(index_diff),
                    'entfernung_km': round(distance, 2),
                    'gradient': round(gradient, 2)
                })
    return results

def calculate_statistics(results):
    if not results:
        return {
            'distance': {'min': 0, 'max': 0, 'avg': 0},
            'diff': {'min': 0, 'max': 0, 'avg': 0},
            'gradient': {'min': 0, 'max': 0, 'avg': 0}
        }
    
    distances = [r['entfernung_km'] for r in results]
    diffs = [r['differenz'] for r in results]
    gradients = [r['gradient'] for r in results]
    
    return {
        'distance': {
            'min': min(distances),
            'max': max(distances),
            'avg': sum(distances) / len(distances)
        },
        'diff': {
            'min': min(diffs),
            'max': max(diffs),
            'avg': sum(diffs) / len(diffs)
        },
        'gradient': {
            'min': min(gradients),
            'max': max(gradients),
            'avg': sum(gradients) / len(gradients)
        }
    }
        
def main():
    # Daten laden
    with open('docs/schools.json', 'r', encoding='utf-8') as f:
        schools_data = json.load(f)
    
    schools_df = pd.DataFrame(schools_data)
    
    # Filtere Schulen mit Sozialindex
    schools_df = schools_df[schools_df['sozialindex'].notna()]
    
    grundschulen_df = schools_df[schools_df['schultyp'] == 'Grundschule']
    weiterfuehrende_df = schools_df[schools_df['schultyp'].isin([
        'Hauptschule', 'Realschule', 'Sekundarschule', 'Gesamtschule', 'Gymnasium'
    ])]
       
    # Daten aufbereiten
    grundschulen_df = prepare_dataframe(grundschulen_df)
    weiterfuehrende_df = prepare_dataframe(weiterfuehrende_df)
    
    # Analyse
    print(f"Analysiere {len(grundschulen_df)} Grundschulen")
    grundschul_results = analyze_schools(grundschulen_df)

    print(f"Analysiere {len(weiterfuehrende_df)} weiterführende Schulen")
    weiterfuehrende_results = analyze_schools(weiterfuehrende_df)

    # Sortierung
    grundschul_results.sort(key=lambda x: x['gradient'], reverse=True)
    weiterfuehrende_results.sort(key=lambda x: x['gradient'], reverse=True)

    # Speichere Ergebnisse aufgeteilt nach Schultyp und Distanz-Bereichen
    distanz_bereiche = {
        '0-1': lambda d: d <= 1,
        '1-2': lambda d: 1 < d <= 2,
        '2-3': lambda d: 2 < d <= 3,
        '3-4': lambda d: 3 < d <= 4,
        '4-5': lambda d: 4 < d <= 5
    }
    
    # Gruppiere Grundschul-Gradienten nach Distanz
    for range_key, range_func in distanz_bereiche.items():
        filtered = [g for g in grundschul_results if range_func(g['entfernung_km'])]
        filename = f'docs/schools-gradients-gs-{range_key}km.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        print(f"Gespeichert: {filename} ({len(filtered)} Gradienten)")
    
    # Gruppiere Weiterführende-Gradienten nach Distanz
    for range_key, range_func in distanz_bereiche.items():
        filtered = [g for g in weiterfuehrende_results if range_func(g['entfernung_km'])]
        filename = f'docs/schools-gradients-wf-{range_key}km.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        print(f"Gespeichert: {filename} ({len(filtered)} Gradienten)")
        
    # Berechne Statistiken für beide Schultypen
    gs_stats = calculate_statistics(grundschul_results)
    ws_stats = calculate_statistics(weiterfuehrende_results)
    
    # Ausgabe der Statistiken
    print("\nAnalyse-Statistiken für Grundschulen:")
    print(f"Anzahl analysierter Schulen: {len(grundschulen_df)}")
    print(f"Anzahl gefundener Schulpaare (mit Mindestdifferenz 3): {len(grundschul_results)}")
    print("\nEntfernungen zwischen Schulpaaren:")
    print(f"  Minimum: {gs_stats['distance']['min']:.2f} km")
    print(f"  Maximum: {gs_stats['distance']['max']:.2f} km")
    print(f"  Durchschnitt: {gs_stats['distance']['avg']:.2f} km")
    print("\nSozialindex-Differenzen:")
    print(f"  Minimum: {gs_stats['diff']['min']}")
    print(f"  Maximum: {gs_stats['diff']['max']}")
    print(f"  Durchschnitt: {gs_stats['diff']['avg']:.1f}")
    print("\nGradienten (Sozialindex-Differenz pro km):")
    print(f"  Minimum: {gs_stats['gradient']['min']:.2f}")
    print(f"  Maximum: {gs_stats['gradient']['max']:.2f}")
    print(f"  Durchschnitt: {gs_stats['gradient']['avg']:.2f}")
    
    print("\nAnalyse-Statistiken für weiterführende Schulen:")
    print(f"Anzahl analysierter Schulen: {len(weiterfuehrende_df)}")
    print(f"Anzahl gefundener Schulpaare (mit Mindestdifferenz 3): {len(weiterfuehrende_results) }")
    print("\nEntfernungen zwischen Schulpaaren:")
    print(f"  Minimum: {ws_stats['distance']['min']:.2f} km")
    print(f"  Maximum: {ws_stats['distance']['max']:.2f} km")
    print(f"  Durchschnitt: {ws_stats['distance']['avg']:.2f} km")
    print("\nSozialindex-Differenzen:")
    print(f"  Minimum: {ws_stats['diff']['min']}")
    print(f"  Maximum: {ws_stats['diff']['max']}")
    print(f"  Durchschnitt: {ws_stats['diff']['avg']:.1f}")
    print("\nGradienten (Sozialindex-Differenz pro km):")
    print(f"  Minimum: {ws_stats['gradient']['min']:.2f}")
    print(f"  Maximum: {ws_stats['gradient']['max']:.2f}")
    print(f"  Durchschnitt: {ws_stats['gradient']['avg']:.2f}")

    print(f"\n{len(grundschul_results) + len(weiterfuehrende_results)} Ergebnisse gespeichert")

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Laufzeit: {end_time - start_time:.2f} Sekunden")