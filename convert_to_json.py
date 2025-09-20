import csv
import json

def convert_csv_to_json():
    schools = []
    
    with open('schulen-mit-koordinaten.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            schools.append({
                'name': row['Schulname'],
                'schultyp': row['Schulform'],
                'sozialindex': row['Sozialindex'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'address': row['found_address']
            })
    
    with open('schools.json', 'w', encoding='utf-8') as file:
        json.dump(schools, file, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    convert_csv_to_json()
