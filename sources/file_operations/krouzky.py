import pandas as pd
import numpy as np

import sources.config as config
import sources.global_functions as global_functions


def krouzky_a_forma_z_oboru_predmetu(df, katedra, semestr, rok):
    # Načte se hlavní dataframe a další potřebná data 
    df_krouzky = pd.read_excel(config.dest_krouzky, dtype=str)
    df_krouzky['Počet studentů kroužku'] = df_krouzky['Počet studentů kroužku'].astype(int)
    df_krouzky['Počet studentů kroužku'] = df_krouzky['Počet studentů kroužku'].replace(-121, 0) #Ve vstupním souboru je číslo -121 použito pro označení, že kroužek je prázdný

    # Vytvoří pomocný dataframe, pro každý předmět se v něm připojí všechny jeho obory 
    df_predmet_info = pd.concat([
        pd.read_csv(global_functions.getPredmetInfo(str(zkratka)), sep=config.separator, engine='python', keep_default_na=False, dtype=str)
        .assign(zkratka=zkratka)
        for zkratka in df["zkratka"]
    ], ignore_index=True)

    #Z předchozího dataframu se vymažou řádky bez doporučeného ročníku
    df_predmet_info['doporucenyRocnik'] = df_predmet_info['doporucenyRocnik'].replace(r'^\s*$', np.nan, regex=True)
    df_predmet_info = df_predmet_info.dropna(subset=['doporucenyRocnik'])

    #Pokud je předmět součástí prezenčních i kombinovaných oborů, jeho forma se změní na Mix
    df_predmet_info['formaProgramu'] = df_predmet_info.groupby('zkratka')['formaProgramu'].transform(
        lambda x: x if x.nunique() == 1 else 'Mix'
    )

    df_predmet_info['formaProgramu'] = df_predmet_info['formaProgramu'].apply(lambda x: global_functions.prepis_formu(x))
    # Sdružení kroužků a předmětů + agregace na 1 řádek = 1 předmět
    df_final = pd.merge(df_predmet_info, df_krouzky, left_on=['kodProgramu', 'formaProgramu', 'doporucenyRocnik'], 
                        right_on=['Program', 'Forma', 'Ročník'], how='left')
    df_final = df_final.groupby('zkratka').agg({
        'Kód kroužku': lambda x: list(x.dropna().unique()), 
        'Počet studentů kroužku': 'sum',  
        'formaProgramu': 'first'  
    }).reset_index()  

    df_final = pridej_minor_krouzky(df_final, df_krouzky)

    # Nakonec připsání kroužků, jejich součtů studentů a formy do výsledného dataframu
    df_merged = pd.merge(df, df_final[['zkratka', 'Kód kroužku A', 'Počet studentů kroužku A', 'formaProgramu']], on='zkratka', how='right')
    df_merged = df_merged.rename(columns={'formaProgramu': 'forma', 'Kód kroužku A': 'krouzky', 'Počet studentů kroužku A': 'pocetStudentu'})
    df_merged['krouzky'] = df_merged['krouzky'].apply(lambda x: ','.join(x))

    df_merged['forma'] = df_merged['forma'].replace({
        'PS': 'Prezenční',
        'KS': 'Kombinovaná',
        'MIX': 'Mix'
    })

    return df_merged

#Přidávání minor koužků momentálně pomocí hledání anagramů - TODO změnit na pevně daný dict
def pridej_minor_krouzky(df_vstup, df_krouzky):
    #Jelikož oba dataframy mají stejně pojmenované sloupce, přejmenují se na unikátní
    df_vstup = df_vstup.rename(columns={'Kód kroužku': 'Kód kroužku A', 'Počet studentů kroužku': 'Počet studentů kroužku A'})
    df_krouzky = df_krouzky.rename(columns={'Kód kroužku': 'Kód kroužku B', 'Počet studentů kroužku': 'Počet studentů kroužku B'})
    #Protože se hledají anagramy, začne se seřazením názvů kroužků
    df_krouzky['Sorted kódy kroužku B'] = df_krouzky['Kód kroužku B'].apply(global_functions.sort_string)
    for idx, row in df_vstup.iterrows():
        current_codes = row['Kód kroužku A']  
        sorted_codes_df_vstup = [global_functions.sort_string(code) for code in current_codes] 
        matches = df_krouzky[df_krouzky['Sorted kódy kroužku B'].isin(sorted_codes_df_vstup) & ~df_krouzky['Kód kroužku B'].isin(current_codes)]
        new_codes = list(matches['Kód kroužku B'])
        df_vstup.at[idx, 'Kód kroužku A'] = current_codes + new_codes
        additional_students = matches['Počet studentů kroužku B'].sum()
        df_vstup.at[idx, 'Počet studentů kroužku A'] += additional_students

    return df_vstup

