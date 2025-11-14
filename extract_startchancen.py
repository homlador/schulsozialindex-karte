#!/usr/bin/env python3
"""
Extrahiert Schulnummern aus einem PDF und ergänzt eine vorhandene CSV um eine Spalte `Startchancen-Schule` mit 1 bzw 0 je Zeile.
"""
import pdfplumber
import pandas as pd
import argparse
import re

def extract_school_numbers(pdf_path):
    """
    Extrahiert Schulnummern aus der PDF-Datei des Startchancen-Programms.
    """
    school_numbers = set()
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            print(text)
            # Suche nach Schulnummern im Format 166472 (6-stellig)
            numbers = re.findall(r'\b\d{6}', text)
            school_numbers.update(numbers)
    
    return school_numbers

def update_csv_with_startchancen(csv_path, school_numbers, output_path):
    """
    Aktualisiert die CSV-Datei mit den Startchancen-Schulen.
    """
    # CSV-Datei einlesen
    df = pd.read_csv(csv_path)
    
    # Neue Spalte 'Startchancen-Schule' hinzufügen
    df['Startchancen-Schule'] = df['Schulnummer'].astype(str).isin(school_numbers).astype(int)
    
    # Aktualisierte CSV-Datei speichern
    df.to_csv(output_path, index=False)
    
    # Statistik ausgeben
    total_startchancen = df['Startchancen-Schule'].sum()
    print(f"\nStatistik:")
    print(f"Gefundene Startchancen-Schulen: {total_startchancen}")
    print(f"Gesamtanzahl Schulen: {len(df)}")
    print(f"Anteil Startchancen-Schulen: {(total_startchancen/len(df)*100):.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Extrahiere Startchancen-Schulen aus PDF und aktualisiere CSV.')
    parser.add_argument('--pdf', required=True, help='Pfad zur PDF-Datei mit Startchancen-Schulen')
    parser.add_argument('--csv', required=True, help='Pfad zur CSV-Datei mit Schulverzeichnis')
    
    args = parser.parse_args()
    
    output_path = args.csv.replace('.csv', '_und_Startchancen.csv')
    
    print("Extrahiere Schulnummern aus PDF...")
    school_numbers = extract_school_numbers(args.pdf)
    print(f"Gefundene Schulnummern: {len(school_numbers)}")
    
    print("\nAktualisiere CSV-Datei...")
    update_csv_with_startchancen(args.csv, school_numbers, output_path)
    
    print(f"\nErgebnis wurde gespeichert in: {output_path}")

if __name__ == '__main__':
    main()