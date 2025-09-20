import pdfplumber
import pandas as pd
import re

def extract_school_info(line):
    """Extrahiert Schulinformationen aus einer Zeile"""
    try:
        # Regulärer Ausdruck für eine 6-stellige Zahl am Anfang
        match = re.match(r'(\d{6})\s+(.*?)\s+(\d+)$', line.strip())
        if match:
            schulnummer, rest, sozialindex = match.groups()
            return {
                'Schulnummer': schulnummer,
                'Schulname': rest.strip(),
                'Sozialindex': sozialindex
            }
    except Exception as e:
        print(f"Fehler beim Verarbeiten der Zeile: {line}")
        print(f"Fehler: {str(e)}")
    return None

def find_schulform(text):
    """Findet die Schulform in einem Text"""
    schulformen = ['Grundschule', 'Hauptschule', 'Realschule', 'Gymnasium', 'Gesamtschule', 'Sekundarschule']
    for form in schulformen:
        if form in text:
            return form, text.index(form)
    return None, -1

def process_page(text, debug=False):
    """Verarbeitet den Text einer Seite"""
    if debug:
        print("=== Seiteninhalt ===")
        print(text)
        print("==================")
    
    current_bezirk = None
    current_kreis = None
    current_schulform = None
    schools = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        
        if debug:
            print(f"\nVerarbeite Zeile: {line}")
        
        # Überspringe Überschriften und leere Zeilen
        if not line or "Übersicht über" in line or "Bezirksregierung" in line or "Seite" in line:
            continue
        
        # Direkter Match für Schulnummer am Anfang
        if re.match(r'^\d{6}', line):
            if debug:
                print(f"Gefundene Schulnummer in Zeile: {line}")
            school_info = extract_school_info(line)
            if school_info and current_bezirk and current_kreis and current_schulform:
                school_info.update({
                    'Bezirksregierung': current_bezirk,
                    'Kreis/Stadt': current_kreis,
                    'Schulform': current_schulform
                })
                schools.append(school_info)
                if debug:
                    print(f"Extrahierte Schule: {school_info}")
                    
        # Erkennt Bezirksregierung oder neue Schulform
        else:
            # Neue Bezirksregierung
            if line.startswith('BR '):
                parts = line.split()
                current_bezirk = parts[1]
                
                # Finde Schulform
                schulform, schulform_idx = find_schulform(line)
                if schulform:
                    current_schulform = schulform
                    # Extrahiere Kreis/Stadt
                    kreis_part = line[len('BR ' + current_bezirk):schulform_idx].strip()
                    current_kreis = kreis_part
                    
                    if debug:
                        print(f"Neue Bezirksregierung: {current_bezirk}")
                        print(f"Neuer Kreis: {current_kreis}")
                        print(f"Neue Schulform: {current_schulform}")
                    
                    # Extrahiere erste Schule aus der Zeile
                    rest = line[schulform_idx + len(current_schulform):].strip()
                    if rest:
                        school_info = extract_school_info(rest)
                        if school_info:
                            school_info.update({
                                'Bezirksregierung': current_bezirk,
                                'Kreis/Stadt': current_kreis,
                                'Schulform': current_schulform
                            })
                            schools.append(school_info)
                            if debug:
                                print(f"Extrahierte Schule aus BR-Zeile: {school_info}")
                    
            # Neue Schulform
            else:
                schulform, schulform_idx = find_schulform(line)
                if schulform:
                    current_schulform = schulform
                    if debug:
                        print(f"Neue Schulform: {current_schulform}")
                        
                    kreis_part = line[:schulform_idx].strip()
                    if kreis_part:
                        current_kreis = kreis_part
                        if debug:
                            print(f"Extrahierter Kreis/Stadt: {current_kreis}")
                            
                    # Extrahiere erste Schule aus der Zeile
                    rest = line[schulform_idx + len(schulform):].strip()
                    if rest:
                        school_info = extract_school_info(rest)
                        if school_info:
                            school_info.update({
                                'Bezirksregierung': current_bezirk,
                                'Kreis/Stadt': current_kreis,
                                'Schulform': current_schulform
                            })
                            schools.append(school_info)
                            if debug:
                                print(f"Extrahierte Schule aus Schulform-Zeile: {school_info}")

    return schools

# PDF einlesen
all_schools = []
with pdfplumber.open('sozialindex_schulliste_schuljahr_2025-26.pdf') as pdf:    
    # Restliche Seiten normal verarbeiten
    for page_num, page in enumerate(pdf.pages, 1):
        print(f"Verarbeite Seite {page_num}")
        text = page.extract_text()
        schools = process_page(text, debug=False)
        all_schools.extend(schools)

# Erstelle DataFrame und speichere als CSV
if all_schools:
    df = pd.DataFrame(all_schools)
    # Ordne die Spalten
    columns_order = ['Bezirksregierung', 'Kreis/Stadt', 'Schulform', 'Schulnummer', 'Schulname', 'Sozialindex']
    df = df[columns_order]
    
    print("\nExtrahierte Daten (erste 10 Zeilen):")
    print(df.head(10))
    df.to_csv('alle_schulen.csv', index=False)
    print(f"\nAnzahl der extrahierten Schulen: {len(df)}")

