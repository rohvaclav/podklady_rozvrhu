import glob
import os
import re
import pandas as pd
import sources.config as config
import sources.global_functions as global_functions



# Použito pro generaci složeného výsledku na rok
# Sepíše předměty, kroužky a formu jednoho oboru, zaznamenává i info o programu 
def zkombinuj_do_vysledku(obor_idno, program_idno, fakulta, program_kod, obor_cislo, rok, semestr): 
    df = pd.read_csv(global_functions.getPredmetySoubor(obor_idno), sep=config.separator, engine='python', keep_default_na=False, dtype=str)
    if not(df.empty):
        writer = pd.ExcelWriter(config.folder_vysledky + "vysledekOboru" + obor_idno + ".xlsx", engine='xlsxwriter')
        df.to_excel(writer, sheet_name='vysledek', index=False)
        df = pd.read_csv( global_functions.getProgramySoubor(fakulta), sep=config.separator, engine='python', keep_default_na=False, dtype=str)
        df = df[df['stprIdno']==str(program_idno)]
        df.to_excel(writer, sheet_name='program', index=False)
        df = pd.read_csv(global_functions.getOborySoubor(program_idno), sep=config.separator, engine='python', keep_default_na=False, dtype=str)
        df = df[df['oborIdno']==str(obor_idno)]
        temp_forma = df.iloc[0, df.columns.get_loc("forma")]
        df.to_excel(writer, sheet_name='obor', index=False)
        # TODO smazat
        df = pd.read_excel(config.dest_krouzky, keep_default_na=False, dtype=str)
        df = df.drop(df[df["Forma"] != global_functions.prepis_formu(temp_forma)].index)
        df = df.drop(df[df.Program != str(program_kod)].index)
        # Užší filtrování podle čísla oboru zústává zakomentované, jelikož některé fakulty tuto kolonku v datech používají k jiným účelům.  
        #df = df.drop(df[(df['Obor'] != str(obor_cislo)) & (df['Obor'] != "")].index)

        df.to_excel(writer, sheet_name='krouzky', index=False)
        writer.close()

# Zkombinuje výsledky předchozí funkce do jednoho velkého souboru 
def zkombinuj_vysledky(rok):
    all_files = glob.glob(os.path.join(config.folder_vysledky, "*.xlsx"))
    df = pd.concat((pd.read_excel(f, dtype=str) for f in all_files), ignore_index=True)
    df = df.drop_duplicates()
    df.to_excel(global_functions.getSlozenyVysledek(rok), index=False)

# Vytvoří soubor dle požadavku uživatele - první krok k vytvoření požadovaného výsledku
def vysledek_pro_katedru(katedra, semestr, rok):
    df = pd.read_excel(global_functions.getSlozenyVysledek(rok), usecols=['katedra','rok','zkratka','nazevDlouhy','prednasejiciSPodily','cviciciSPodily','seminariciSPodily','jednotekPrednasek','jednotkaPrednasky','jednotekCviceni','jednotkaCviceni','jednotekSeminare','jednotkaSeminare','statut','doporucenyRocnik', 'doporucenySemestr'], dtype=str)
    df = df[(df['katedra']==katedra)]
    del df['katedra']
    #df['zkratka'] = df['zkratka'].astype(str) TODO smazat pokud nejsou problémy
    # TODO - podívat se na to, jestli je kontrola roku potřebná
    df['rok'] = pd.to_numeric(df['rok'])
    df = df[(df['rok']==rok)]
    del df['rok']
    df = df[(df['doporucenySemestr']==semestr)]
    df = df.drop_duplicates()
    #df.to_excel(global_functions.getVysledekKatedry(katedra, semestr, rok), index=False)
    return df