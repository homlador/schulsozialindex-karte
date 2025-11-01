"""
Führt das Schul- und Adressverzeichnis mit den Daten zum Sozialindex zusammen
"""
import pandas as pd

# Excel-Datei mit Schuldaten einlesen
df_schulen = pd.read_excel('AS_BS_Verzeichnis_2024_25_(gerundet)_0.xlsx', sheet_name="AS_BS_Schulverzeichnis 2024_25",  dtype=str)

# CSV-Datei mit Sozialindex einlesen
df_sozialindex  = pd.read_csv('schulliste_sj_25_26_open_data.csv', encoding='latin1', sep=';', dtype=str)

# Führt die Daten anhand der Schulnummer zusammen
# left join, um alle Schulen aus der Schulliste zu behalten
df_merged = pd.merge(
    df_schulen,
    df_sozialindex[['Sozialindexstufe', 'Schulnummer']],
    on='Schulnummer',
    how='left'
)

# Leere Zeilen entfernen
df_merged = df_merged.dropna(subset=['Schulnummer'])

# Spalte Sozialindexstufe umbenennen
df_merged = df_merged.rename(columns={'Sozialindexstufe': 'Sozialindex'})

# Ergebnis speichern
df_merged.to_csv('AS_BS_Verzeichnis_2024_25_mit_Sozialindex.csv', index=False)

print(f"Zusammengeführte Daten wurden in 'AS_BS_Verzeichnis_2024_25_mit_Sozialindex.csv' gespeichert.")
print(f"Anzahl der Schulen in der ursprünglichen Liste: {len(df_schulen)}")
print(f"Anzahl der Schulen mit Sozialindex: {df_merged['Sozialindex'].notna().sum()}")
print(f"Anzahl der Schulen ohne Sozialindex: {df_merged['Sozialindex'].isna().sum()}")