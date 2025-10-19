import pandas as pd
import json
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
                        'sozialindex': int(school1['sozialindex']),
                        'lat': school1['lat'],
                        'lon': school1['lon']
                    },
                    'schule_2': {
                        'name': school2['name'],
                        'schulnummer': school2['schulnummer'],
                        'sozialindex': int(school2['sozialindex']),
                        'lat': school2['lat'],
                        'lon': school2['lon']
                    },
                    'differenz': int(index_diff),
                    'entfernung_km': round(distance, 2),
                    'gradient': round(gradient, 2)
                })
    
    # 3. Top-50 Gradienten extrahieren
    results.sort(key=lambda x: x['gradient'], reverse=True)
    top_50 = results[:50]
    
    # Speichere Ergebnisse
    with open('docs/schools-gradients.json', 'w', encoding='utf-8') as f:
        json.dump(top_50, f, ensure_ascii=False, indent=2)
    
    print(f"Analyse abgeschlossen. {len(top_50)} Schulpaare wurden in schools-gradients.json gespeichert.")

if __name__ == "__main__":
    main()