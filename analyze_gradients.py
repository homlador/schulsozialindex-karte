import pandas as pd
import json
import time
from math import radians, sin, cos, sqrt, atan2

# FIXME: Optimierungspotential: Nachbarschafts-Suche mit BallTree oder ein Räumliches Gitter verwenden, um die Anzahl der Paarvergleiche zu reduzieren.

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

def main():
    # 1. Daten laden
    with open('docs/schools.json', 'r', encoding='utf-8') as f:
        schools_data = json.load(f)
    
    # Konvertiere in DataFrame
    schools_df = pd.DataFrame(schools_data)
    
    # Filtere nur Grundschulen und Schulen mit Sozialindex
    schools_df = schools_df[
        (schools_df['schultyp'] == 'Grundschule') & 
        (schools_df['sozialindex'].str.strip() != '') & 
        (schools_df['sozialindex'].notna())
    ]
    
    print(f"Analysiere {len(schools_df)} Schulen...")
    
    # Konvertiere Koordinaten und Sozialindex zu float
    schools_df['lat'] = schools_df['latitude'].astype(float)
    schools_df['lon'] = schools_df['longitude'].astype(float)
    schools_df['sozialindex'] = pd.to_numeric(schools_df['sozialindex'], errors='coerce')
    
    # 2. Paarvergleiche durchführen
    results = []
    
    for i, school1 in schools_df.iterrows():
        for j, school2 in schools_df.iloc[i+1:].iterrows():
            # Berechne Entfernung
            distance = haversine_distance(
                float(school1['lat']), float(school1['lon']),
                float(school2['lat']), float(school2['lon'])
            )
            
            # Berechne Index-Differenz
            index_diff = abs(school1['sozialindex'] - school2['sozialindex'])
            
            # Berechne Gradient
            gradient = index_diff / distance if distance > 0 else 0
            
            # Speichere Ergebnis
            if index_diff >= 3:  # Mindestdifferenz von 3 Stufen
                results.append({
                    'schule_1': {
                        'name': school1['name'],
                        'schulnummer': school1['schulnummer'],
                        'schultyp': school1['schultyp'],
                        'sozialindex': int(school1['sozialindex']),
                        'lat': school1['lat'],
                        'lon': school1['lon']
                    },
                    'schule_2': {
                        'name': school2['name'],
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
    
    # 3. Top-100 Gradienten extrahieren
    results.sort(key=lambda x: x['gradient'], reverse=True)
    top_results = results[:500]
    
    # Statistiken berechnen
    num_schools = len(schools_df)
    num_pairs = len(results)
    
    # Abstand-Statistiken
    distances = [r['entfernung_km'] for r in results]
    min_distance = min(distances) if distances else 0
    max_distance = max(distances) if distances else 0
    avg_distance = sum(distances) / len(distances) if distances else 0
    
    # Sozialindex-Differenz-Statistiken
    diffs = [r['differenz'] for r in results]
    min_diff = min(diffs) if diffs else 0
    max_diff = max(diffs) if diffs else 0
    avg_diff = sum(diffs) / len(diffs) if diffs else 0
    
    # Gradient-Statistiken
    gradients = [r['gradient'] for r in results]
    min_gradient = min(gradients) if gradients else 0
    max_gradient = max(gradients) if gradients else 0
    avg_gradient = sum(gradients) / len(gradients) if gradients else 0
    
    # Speichere Ergebnisse
    with open('docs/schools-gradients.json', 'w', encoding='utf-8') as f:
        json.dump(top_results, f, ensure_ascii=False, indent=2)
    
    # Ausgabe der Statistiken
    print("\nAnalyse-Statistiken:")
    print(f"Anzahl analysierter Grundschulen: {num_schools}")
    print(f"Anzahl gefundener Schulpaare (mit Mindestdifferenz 3): {num_pairs}")
    print("\nEntfernungen zwischen Schulpaaren:")
    print(f"  Minimum: {min_distance:.2f} km")
    print(f"  Maximum: {max_distance:.2f} km")
    print(f"  Durchschnitt: {avg_distance:.2f} km")
    print("\nSozialindex-Differenzen:")
    print(f"  Minimum: {min_diff}")
    print(f"  Maximum: {max_diff}")
    print(f"  Durchschnitt: {avg_diff:.1f}")
    print("\nGradienten (Sozialindex-Differenz pro km):")
    print(f"  Minimum: {min_gradient:.2f}")
    print(f"  Maximum: {max_gradient:.2f}")
    print(f"  Durchschnitt: {avg_gradient:.2f}")
    
    print(f"\n{len(top_results)} Schulpaare wurden in schools-gradients.json gespeichert.")
    

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Laufzeit: {end_time - start_time:.2f} Sekunden")