import os
import pandas as pd
import sources.config as config
import math
import re
    
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def sort_string(s):
    return ''.join(sorted(s))

def bezpecna_int_konverze(value):
    if isinstance(value, float) and math.isnan(value):
        return None  
    return int(value)

def prepis_formu(x):
    if x in ["KS","kombinované","Kombinované", "kombinovaná", "Kombinovaná"]:
        return "KS"
    elif x in ["PS","prezenční","Prezenční"]:
        return "PS"
    else:
        return "MIX"
    

#dělí číslo na rovnoměrné části, použito pro kroužky jejichž počet studentů přesahuje kapacitu akce 
def rozdel_na_cela_cisla(delenec, kapacita):
    delitel = math.ceil(delenec/kapacita)
    kvocient = delenec // delitel
    zbytek_po_deleni = delenec % delitel
    vysledek = [kvocient] * delitel

    for i in range(zbytek_po_deleni):
        vysledek[i] += 1

    return vysledek

def ziskej_program_data(fakulta, row, setting):
    df = pd.read_csv(getProgramySoubor(fakulta), sep=config.separator, engine='python', dtype=str)
    if(setting=="stprIdno"):
        return str(df.loc[row, "stprIdno"])
    else:
        return str(df.loc[row, "kod"])
    
def ziskej_obor_data(row, idno, setting):
    df = pd.read_csv(getOborySoubor(idno), sep=config.separator, engine='python', dtype=str)
    if(setting=="oborIdno"):
        return str(df.loc[row, "oborIdno"])
    else:
        return str(df.loc[row, "cisloOboru"])

def ziskej_typ_RA(df):
    if(is_number(df['jednotekPrednasek'])):
        return "Př"
    elif(is_number(df['jednotekCviceni'])):
        return "Cv"
    else:
        return "Se"
    
def ziskej_prvni_vyucujici(df, typ):
    match typ:
        case "Př":
            sloupec = 'prednasejiciSPodily'
        case "Cv":
            sloupec = 'cviciciSPodily'
        case "Se":
            sloupec = 'seminariciSPodily'
    if not(re.search(r'\(\d+\)', str(df[sloupec]))):
        vyucujici = str(df[sloupec])
        vyucujici = vyucujici.replace('(100)','')

    else:
        vyucujici_temp = re.split(r'\(\d+\)', str(df[sloupec]))
        vyucujici = vyucujici_temp[0]
    vyucujici = vyucujici.replace('\'','')
    vyucujici = vyucujici.rstrip()
    return vyucujici

    
def filtruj_vysledky(soubor, semestr, katedra):
    uprava = pd.read_csv(soubor,sep=config.separator, engine='python', keep_default_na=False, dtype=str)
    uprava = uprava[uprava['doporucenySemestr']==semestr]
    uprava = uprava[uprava['katedra']==katedra]
    if not uprava.empty:
        uprava.to_csv(soubor, index=False, sep=';', mode='w+')
    else:
        os.remove(soubor)

def filter_rows_by_values(df, col, values):
    return df[~df[col].isin(values)]

def getProgramySoubor(fakulta):
    return config.folder_programy + "studijniProgramy" + fakulta + ".csv"

def getOborySoubor(program_idno):
    return config.folder_obory + "oboryStudijnihoProgramu" + program_idno + ".csv"

def getPredmetySoubor(obor_idno):
    return config.folder_predmety + "predmetyByOborFullInfo" + obor_idno + ".csv"

def getVysledekKatedry(katedra, semestr, rok):
    return config.folder_local + "/vysledekKatedry" + katedra + "_" + semestr + "_" + str(rok) + ".xlsx"

def getPredmetInfo(zkratka):
    return config.folder_predmetInfo + "predmet" + str(zkratka) + ".csv"

def getUcitelInfo(krestni, prijmeni):
    return config.folder_ucitele + "infoUcitel" + krestni + prijmeni + ".csv"

def getRozvrhPredmetu(zkratka, rok):
    return config.folder_rozvrhy + "rozvrhByPredmet_" + zkratka + "_" + rok + ".csv"

def getRozvrhKatedry(katedra, semestr, rok):
    return config.folder_rozvrhy + "rozvrhByKatedra_" + katedra + "_" + str(rok) + "_" + semestr + ".csv"

def getSlozenyVysledek(rok):
    return config.folder + "slozenyVysledek" + str(rok) + ".xlsx"

