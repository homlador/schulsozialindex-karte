"""
Konvertiert die CSV-Datei mit Schulinformationen und Koordinaten in eine JSON-Datei
"""

import csv
import json

def convert_csv_to_json():
    schools = []

    with open('AS_BS_Verzeichnis_2024_25_mit_Sozialindex_und_Koordinaten_und_Startchancen.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        # Nur bestimmte Schulnummern auswählen
        #auswahl_schulnummern = [164306, 164549, 164586, 164598, 164604, 164616, 164641, 164665, 164677, 164847, 165116, 165517, 165979, 165992, 166005, 166017, 166030, 166080, 183532, 185267, 187793, 188177, 188499, 188712, 189261, 189583, 189595, 191395, 191474, 192211, 193252] 
        for row in csv_reader:            
            schools.append({
                'name': row['Amtliche Bezeichnung 1'],
                'schulnummer': row['Schulnummer'],
                'ort': row['Ort'],                
                'schultyp': row['Schulform'],
                'sozialindex': row['Sozialindex'],
                'anzahl': row['Anzahl'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'adresse': row['Straße und Hausnummer'] + ', ' + row['Postleitzahl'] + ' ' + row['Ort'],
                'startchancen': row['Startchancen-Schule']
            }) #if int(row['Schulnummer']) in auswahl_schulnummern else None           
            # Oder nur Schulen aus Duisburg auswählen
            #if row['Ort'] == 'Duisburg' else None
    
    with open('docs/schools.json', 'w', encoding='utf-8') as file:
        json.dump(schools, file, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    convert_csv_to_json()
