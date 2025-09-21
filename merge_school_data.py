"""
Ergänzt Schuldaten um den Sozialindex
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

def clean_schulnummer(series):
    """
    Bereinigt Schulnummern-Spalten - behandelt sowohl numerische als auch Text-Formate
    """
    # Wenn die Serie numerisch ist (int oder float)
    if pd.api.types.is_numeric_dtype(series):
        # Konvertiere NaN zu leeren Strings
        cleaned = series.fillna('')
        # Für numerische Werte: konvertiere zu int (entfernt .0), dann zu string
        mask = (cleaned != '') & (cleaned.notna())
        if mask.any():
            # Konvertiere Float-Werte zu Int, dann zu String
            cleaned_copy = cleaned.copy()
            cleaned_copy.loc[mask] = cleaned_copy.loc[mask].astype(int).astype(str)
            return cleaned_copy.astype(str)
        else:
            return cleaned.astype(str)
    else:
        # Für String-Daten: normale Bereinigung
        cleaned = series.astype(str).str.strip()
        # Entferne .0 am Ende (falls als String mit .0 vorliegt)
        cleaned = cleaned.str.replace(r'\.0$', '', regex=True)
        # Entferne 'nan' Werte
        cleaned = cleaned.replace('nan', '')
        return cleaned

def load_and_merge_school_data():
    """
    Lädt die beiden Dateien und führt sie basierend auf der Schulnummer zusammen
    """
    try:
        # Dateipfade definieren
        hauptdatei = "AS_BS_Verzeichnis_2024_25_(gerundet)_0.xlsx"  # Excel-Datei
        tabellenblatt = "AS_BS_Adressverzeichnis 2024_25"  # Spezifisches Tabellenblatt
        sozialindex_datei = "sozialindex_schulliste_schuljahr_2025-26.csv"
        
        print(f"Lade Hauptdatei '{hauptdatei}', Tabellenblatt '{tabellenblatt}'...")
        
        # Lade Excel-Datei mit spezifischem Tabellenblatt
        try:
            # Lade zuerst normal, um Spalten zu identifizieren
            df_haupt = pd.read_excel(hauptdatei, sheet_name=tabellenblatt)
            
            # Finde potentielle Schulnummer-Spalten und numerische Spalten die als String gespeichert werden sollen
            potential_schulnr_cols = [col for col in df_haupt.columns 
                                    if any(keyword in str(col).lower() 
                                           for keyword in ['schulnummer', 'schul', 'nummer', 'id', 'nr'])]
            
            # Finde Anzahl- und Sozialindex-Spalten
            additional_string_cols = [col for col in df_haupt.columns 
                                    if any(keyword in str(col).lower() 
                                           for keyword in ['anzahl', 'sozial', 'index'])]
            
            # Kombiniere alle Spalten die als String geladen werden sollen
            all_string_cols = list(set(potential_schulnr_cols + additional_string_cols))
            
            # Lade nochmal mit dtype=str für alle relevanten Spalten
            if all_string_cols:
                dtype_dict = {col: str for col in all_string_cols}
                df_haupt = pd.read_excel(hauptdatei, sheet_name=tabellenblatt, dtype=dtype_dict)
                print(f"Als String geladene Spalten: {all_string_cols}")
            else:
                df_haupt = pd.read_excel(hauptdatei, sheet_name=tabellenblatt)
                print("Keine numerischen Spalten für String-Konvertierung erkannt - normale Ladung")
        except ValueError as e:
            print(f"Fehler beim Laden des Tabellenblatts '{tabellenblatt}': {e}")
            print("Verfügbare Tabellenblätter:")
            try:
                xl_file = pd.ExcelFile(hauptdatei)
                for sheet in xl_file.sheet_names:
                    print(f"  - {sheet}")
                print(f"\nBitte passen Sie das Tabellenblatt im Skript an oder verwenden Sie eines der verfügbaren Blätter.")
                return None
            except Exception:
                print("Konnte verfügbare Tabellenblätter nicht auflisten.")
                return None
        except Exception as e:
            print(f"Fehler beim Laden der Excel-Datei: {e}")
            return None
        
        print("Lade Sozialindex-Datei...")
        try:
            # Lade CSV mit String-Konvertierung für relevante Spalten
            # Zuerst normal laden um Spalten zu identifizieren
            df_temp = pd.read_csv(sozialindex_datei, encoding='utf-8', nrows=0)  # Nur Header
            potential_schulnr_cols_csv = [col for col in df_temp.columns 
                                         if any(keyword in str(col).lower() 
                                                for keyword in ['schulnummer', 'schul', 'nummer', 'id', 'nr'])]
            
            # Finde auch Anzahl- und Sozialindex-Spalten in CSV
            additional_string_cols_csv = [col for col in df_temp.columns 
                                        if any(keyword in str(col).lower() 
                                               for keyword in ['anzahl', 'sozial', 'index'])]
            
            # Kombiniere alle Spalten
            all_string_cols_csv = list(set(potential_schulnr_cols_csv + additional_string_cols_csv))
            
            if all_string_cols_csv:
                dtype_dict_csv = {col: str for col in all_string_cols_csv}
                df_sozial = pd.read_csv(sozialindex_datei, encoding='utf-8', dtype=dtype_dict_csv)
                print(f"CSV als String geladene Spalten: {all_string_cols_csv}")
            else:
                df_sozial = pd.read_csv(sozialindex_datei, encoding='utf-8')
                print("CSV: Keine relevanten Spalten für String-Konvertierung erkannt - normale Ladung")
        except UnicodeDecodeError:
            try:
                df_sozial = pd.read_csv(sozialindex_datei, encoding='latin1')
            except Exception as e:
                print(f"Fehler beim Laden der Sozialindex-Datei: {e}")
                return None
        except Exception as e:
            print(f"Fehler beim Laden der Sozialindex-Datei: {e}")
            return None
        
        print(f"Hauptdatei geladen: {len(df_haupt)} Zeilen, {len(df_haupt.columns)} Spalten")
        print(f"Sozialindex-Datei geladen: {len(df_sozial)} Zeilen, {len(df_sozial.columns)} Spalten")
        
        # Spalten anzeigen um die richtige Schulnummer-Spalte zu identifizieren
        print("\nSpalten in der Hauptdatei:")
        print(df_haupt.columns.tolist())
        
        print("\nSpalten in der Sozialindex-Datei:")
        print(df_sozial.columns.tolist())
        
        # Automatische Erkennung der Schulnummer-Spalten
        schulnummer_spalten_haupt = [col for col in df_haupt.columns if 'schulnummer' in str(col).lower() or ('schul' in str(col).lower() and 'nummer' in str(col).lower())]
        schulnummer_spalten_sozial = [col for col in df_sozial.columns if 'schulnummer' in str(col).lower() or ('schul' in str(col).lower() and 'nummer' in str(col).lower())]
        
        # Erweiterte Suche nach möglichen ID-Spalten
        if not schulnummer_spalten_haupt:
            id_spalten_haupt = [col for col in df_haupt.columns if any(keyword in str(col).lower() for keyword in ['id', 'nummer', 'nr', 'schule'])]
            if id_spalten_haupt:
                print(f"\nMögliche ID-Spalten in der Hauptdatei: {id_spalten_haupt}")
                schulnummer_spalten_haupt = id_spalten_haupt
        
        if not schulnummer_spalten_sozial:
            id_spalten_sozial = [col for col in df_sozial.columns if any(keyword in str(col).lower() for keyword in ['id', 'nummer', 'nr', 'schule'])]
            if id_spalten_sozial:
                print(f"\nMögliche ID-Spalten in der Sozialindex-Datei: {id_spalten_sozial}")
                schulnummer_spalten_sozial = id_spalten_sozial
        
        if not schulnummer_spalten_haupt:
            print("\nWARNUNG: Keine Schulnummer-Spalte in der Hauptdatei automatisch erkannt.")
            print("Verfügbare Spalten:", df_haupt.columns.tolist())
            schulnummer_spalte_haupt = input("Bitte geben Sie den Namen der Schulnummer-Spalte in der Hauptdatei ein: ")
        else:
            schulnummer_spalte_haupt = schulnummer_spalten_haupt[0]
            print(f"\nVerwende Schulnummer-Spalte in Hauptdatei: '{schulnummer_spalte_haupt}'")
        
        if not schulnummer_spalten_sozial:
            print("\nWARNUNG: Keine Schulnummer-Spalte in der Sozialindex-Datei automatisch erkannt.")
            print("Verfügbare Spalten:", df_sozial.columns.tolist())
            schulnummer_spalte_sozial = input("Bitte geben Sie den Namen der Schulnummer-Spalte in der Sozialindex-Datei ein: ")
        else:
            schulnummer_spalte_sozial = schulnummer_spalten_sozial[0]
            print(f"Verwende Schulnummer-Spalte in Sozialindex-Datei: '{schulnummer_spalte_sozial}'")
        
        # Sozialindex-Spalte identifizieren
        sozialindex_spalten = [col for col in df_sozial.columns if 'sozial' in str(col).lower() and 'index' in str(col).lower()]
        if not sozialindex_spalten:
            sozialindex_spalten = [col for col in df_sozial.columns if 'index' in str(col).lower()]
        
        if not sozialindex_spalten:
            print("\nVerfügbare Spalten in Sozialindex-Datei:", df_sozial.columns.tolist())
            sozialindex_spalte = input("Bitte geben Sie den Namen der Sozialindex-Spalte ein: ")
        else:
            sozialindex_spalte = sozialindex_spalten[0]
            print(f"Verwende Sozialindex-Spalte: '{sozialindex_spalte}'")
        
        # DEBUG: Zeige Datentypen und Beispielwerte VOR der Bereinigung
        print(f"\n--- DEBUG INFORMATION ---")
        print(f"Hauptdatei - Spalte '{schulnummer_spalte_haupt}':")
        print(f"  Datentyp: {df_haupt[schulnummer_spalte_haupt].dtype}")
        print(f"  Beispiel-Rohwerte: {df_haupt[schulnummer_spalte_haupt].head().tolist()}")
        print(f"  Beispiel-Repr: {[repr(x) for x in df_haupt[schulnummer_spalte_haupt].head().tolist()]}")
        
        print(f"\nSozialindex-Datei - Spalte '{schulnummer_spalte_sozial}':")
        print(f"  Datentyp: {df_sozial[schulnummer_spalte_sozial].dtype}")
        print(f"  Beispiel-Rohwerte: {df_sozial[schulnummer_spalte_sozial].head().tolist()}")
        print(f"  Beispiel-Repr: {[repr(x) for x in df_sozial[schulnummer_spalte_sozial].head().tolist()]}")
        
        # Bereinige die Schulnummern
        print(f"\nBereinige Schulnummern...")
        df_haupt[schulnummer_spalte_haupt] = clean_schulnummer(df_haupt[schulnummer_spalte_haupt])
        df_sozial[schulnummer_spalte_sozial] = clean_schulnummer(df_sozial[schulnummer_spalte_sozial])
        
        # DEBUG: Zeige Werte NACH der Bereinigung
        print(f"\nNach der Bereinigung:")
        print(f"Hauptdatei - Beispiel-Werte: {df_haupt[schulnummer_spalte_haupt].head().tolist()}")
        print(f"Sozialindex - Beispiel-Werte: {df_sozial[schulnummer_spalte_sozial].head().tolist()}")
        
        # Zeige einige gemeinsame Werte zum Vergleich
        haupt_unique = set(df_haupt[schulnummer_spalte_haupt].dropna().unique())
        sozial_unique = set(df_sozial[schulnummer_spalte_sozial].dropna().unique())
        gemeinsame = haupt_unique.intersection(sozial_unique)
        
        print(f"\n--- VERGLEICH ---")
        print(f"Eindeutige Schulnummern in Hauptdatei: {len(haupt_unique)}")
        print(f"Eindeutige Schulnummern in Sozialindex-Datei: {len(sozial_unique)}")
        print(f"Gemeinsame Schulnummern: {len(gemeinsame)}")
        
        if gemeinsame:
            print(f"Beispiele gemeinsamer Schulnummern: {list(gemeinsame)[:10]}")
        
        # Merge durchführen
        print(f"\nFühre Zusammenführung durch...")
        df_merged = df_haupt.merge(
            df_sozial[[schulnummer_spalte_sozial, sozialindex_spalte]], 
            left_on=schulnummer_spalte_haupt, 
            right_on=schulnummer_spalte_sozial, 
            how='left'
        )
        
        # Statistiken anzeigen
        print(f"\n--- ERGEBNIS ---")
        print(f"Ursprüngliche Zeilen: {len(df_haupt)}")
        print(f"Zeilen nach Merge: {len(df_merged)}")
        print(f"Schulen mit Sozialindex gefunden: {df_merged[sozialindex_spalte].notna().sum()}")
        print(f"Schulen ohne Sozialindex: {df_merged[sozialindex_spalte].isna().sum()}")
        print(f"Erfolgsquote: {(df_merged[sozialindex_spalte].notna().sum() / len(df_merged) * 100):.1f}%")
        
        # Duplikat-Spalte entfernen falls vorhanden
        if schulnummer_spalte_sozial in df_merged.columns and schulnummer_spalte_sozial != schulnummer_spalte_haupt:
            df_merged = df_merged.drop(columns=[schulnummer_spalte_sozial])
        
        # Schulen ohne Sozialindex anzeigen (falls vorhanden)
        missing_count = df_merged[sozialindex_spalte].isna().sum()
        if missing_count > 0:
            print(f"\nSchulen ohne gefundenen Sozialindex ({missing_count} von {len(df_merged)}):")
            missing_schools = df_merged[df_merged[sozialindex_spalte].isna()][schulnummer_spalte_haupt].unique()
            for i, school in enumerate(missing_schools[:10]):  # Zeige nur die ersten 10
                print(f"- {school}")
            if len(missing_schools) > 10:
                print(f"... und {len(missing_schools) - 10} weitere")
        
        # Ergebnis speichern
        # output_file = "AS_BS_Verzeichnis_2024_25_mit_Sozialindex.xlsx"
        # df_merged.to_excel(output_file, index=False, sheet_name="Daten_mit_Sozialindex")
        # print(f"\nErgebnis gespeichert als: {output_file}")
        
        # CSV-Version speichern
        csv_output = "AS_BS_Verzeichnis_2024_25_mit_Sozialindex.csv"
        df_merged.to_csv(csv_output, index=False, encoding='utf-8')
        print(f"CSV-Version gespeichert als: {csv_output}")
        
        return df_merged
        
    except FileNotFoundError as e:
        print(f"Fehler: Datei nicht gefunden - {e}")
        print("Bitte stellen Sie sicher, dass beide Dateien im aktuellen Verzeichnis sind:")
        print(f"- {hauptdatei}")
        print(f"- {sozialindex_datei}")
        return None
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Hauptfunktion
    """
    print("Schuldaten-Merger - Ergänzung um Sozialindex")
    print("=" * 50)
    print(f"Excel-Datei: AS_BS_Verzeichnis_2024_25_(gerundet)_0.xlsx")
    print(f"Tabellenblatt: AS_BS_Adressverzeichnis 2024_25")
    print(f"Sozialindex-Datei: sozialindex_schulliste_schuljahr_2025-26.csv")
    print("=" * 50)
    
    result = load_and_merge_school_data()
    
    if result is not None:
        print("\n" + "=" * 50)
        print("Zusammenführung erfolgreich abgeschlossen!")
        
        # Zusätzliche Analyse
        print("\nZusätzliche Informationen:")
        sozial_cols = [col for col in result.columns if 'sozial' in str(col).lower() and 'index' in str(col).lower()]
        if not sozial_cols:
            sozial_cols = [col for col in result.columns if 'index' in str(col).lower()]
            
        if sozial_cols:
            sozial_col = sozial_cols[0]
            print(f"\nVerteilung des Sozialindex ({sozial_col}):")
            value_counts = result[sozial_col].value_counts().sort_index()
            for index_value, count in value_counts.items():
                print(f"  Index {index_value}: {count} Schulen")
                
            # Prozentuale Verteilung
            print(f"\nProzentuale Verteilung:")
            percentages = result[sozial_col].value_counts(normalize=True).sort_index() * 100
            for index_value, percentage in percentages.items():
                print(f"  Index {index_value}: {percentage:.1f}%")
    else:
        print("\nFehler beim Zusammenführen der Daten.")
        print("Bitte überprüfen Sie:")
        print("- Ob beide Dateien existieren")
        print("- Ob der Tabellenblattname korrekt ist")
        print("- Ob die Spaltenbezeichnungen stimmen")

if __name__ == "__main__":
    main()
