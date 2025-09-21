"""
Konvertiert die CSV-Datei mit Schulinformationen und Koordinaten in eine JSON-Datei
"""

import csv
import json

def convert_csv_to_json():
    schools = []
    
    with open('schulen-mit-koordinaten.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
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
                'address': row['found_address']
            }) #if row['Ort'] == 'Duisburg' else None
    
    with open('docs/schools-duisburg.json', 'w', encoding='utf-8') as file:
        json.dump(schools, file, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    convert_csv_to_json()
