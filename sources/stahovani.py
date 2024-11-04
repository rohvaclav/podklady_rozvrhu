from io import StringIO
import os
from urllib.request import urlretrieve
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth 
import sources.config as config
import sources.global_functions as global_functions
from main import get_user_ticket
from main import refresh_url


def save_csv(url, params, file_name, destination, columnList=None):
    response = requests.get(url, params=params, auth=HTTPBasicAuth(get_user_ticket(),''))
    if(response.text=="Unauthorized - invalid authorization data"):
        print("ERROR: Vypršela platnost ticketu") 
        refresh_url() # TODO
    df = pd.read_csv(StringIO(response.text), sep=";", engine='python', na_filter = False, dtype=str) 
    df.to_csv(destination + f"{file_name}.csv", index=False, sep=';', columns=columnList)

def stahni_studijni_programy(fakulta, rok):
    stag_vars = {
    "lang" : "cs",
    "outputFormat" : "CSV",
    "pouzePlatne" : "true",
    "fakulta" : fakulta,
    "rok" : rok,
    "outputFormatEncoding" : "utf-8",
    }
    save_csv("https://ws.ujep.cz/ws/services/rest2/programy/getStudijniProgramy", stag_vars, "studijniProgramy" + fakulta, config.folder_programy, ['stprIdno', 'nazevCz', 'kod', 'typ', 'forma', 'fakulta', 'platnyOd', 'neplatnyOd', 'garant', 'garantUcitIdno', 'akreditaceOdDate', 'akreditaceDoDate'])

def stahni_obory_programu(program):
    stag_vars = {
    "lang" : "cs",
    "outputFormat" : "CSV",
    "outputFormatEncoding" : "utf-8",
    "stprIdno" : program,
    }
    save_csv("https://ws.ujep.cz/ws/services/rest2/programy/getOboryStudijnihoProgramu", 
    stag_vars , "oboryStudijnihoProgramu" + program, config.folder_obory, 
    ['oborIdno','nazevCz','cisloOboru','cisloSpecializace','typ','forma','fakulta','platnyOd','neplatnyOd','stprIdno','garant','garantUcitIdno','nazevProgramu','kodProgramu'])


def stahni_predmety_oboru(obor, rok):
    stag_vars = {
    "lang" : "cs",
    "outputFormat" : "CSV",
    "outputFormatEncoding" : "utf-8",
    "oborIdno" : obor,
    "rok" : rok,
    }
    save_csv("https://ws.ujep.cz/ws/services/rest2/predmety/getPredmetyByOborFullInfo", stag_vars , "predmetyByOborFullInfo" + obor, config.folder_predmety, ['katedra', 'zkratka', 'rok', 'nazevDlouhy', 'vyukaZS', 'vyukaLS', 'kreditu', 'garantiSPodily', 'garantiUcitIdno', 'prednasejiciSPodily', 'cviciciSPodily', 'seminariciSPodily', 'podminujiciPredmety', 'vylucujiciPredmety', 'jednotekPrednasek','jednotkaPrednasky','jednotekCviceni','jednotkaCviceni','jednotekSeminare','jednotkaSeminare', 'statut','doporucenyRocnik','doporucenySemestr','vyznamPredmetu'])

def stahni_rozvrh_katedry(katedra, semestr, rok):
    if not(os.path.isfile(global_functions.getRozvrhKatedry(katedra, semestr, rok))):
        stag_vars = {
        "lang" : "cs",
        "outputFormat" : "CSV",
        "outputFormatEncoding" : "utf-8",
        "katedra" : katedra,
        "jenRozvrhoveAkce" : True,
        "rok" : str(rok),
        "semestr" : semestr,
        }
        save_csv("https://ws.ujep.cz/ws/services/rest2/rozvrhy/getRozvrhByKatedra", stag_vars,
         "rozvrhByKatedra_" + katedra + "_" + str(rok) + "_" + semestr, config.folder_rozvrhy)

def stahni_krouzky(rok):
    #Stahování - data o kroužcích stáhne ze STAGu. Nefunkční, jelikož nemá data o počtu studentů
    if(config.krouzky_rezim == "stahovani"):
        url="https://portal.ujep.cz/StagPortletsJSR168/ProhlizeniPrint?stateClass=cz.zcu.stag.portlets168.prohlizeni.krouzek.KrouzekSearchState&krouzekSearchKod=&rokInput=" + rok + "&krouzekSearchFakulta=&krouzekSearchRocnik=&krouzekSearchMisto=&programInput=&oborInput=&zkratkaKombinaceInput=&xlsxSearchExport=A"
        urlretrieve(url, config.dest_krouzky)
        upraveneKrouzky = pd.read_excel(config.dest_krouzky, skiprows=list(range(1,2)), dtype=str)
        upraveneKrouzky['Počet studentů kroužku'] = ""
    #Data o kroužcích z manuálně přiloženého souboru
    elif(config.krouzky_rezim == "ze_souboru"):
        upraveneKrouzky = pd.read_excel(config.folder + "kontrolaVystupu.xlsx", skiprows=list(range(1,2)), dtype=str)
    newUpravaFormy = upraveneKrouzky['Popis'].apply(global_functions.prepis_formu)
    for index, row in upraveneKrouzky.iterrows():
        # oprava pro neshody forem - forma kroužku má vyšší prioritu
        if(("KS" in row['Kód kroužku']) & (newUpravaFormy[index] != "KS")):
            newUpravaFormy[index] = "KS"
     
    upraveneKrouzky['Forma'] = newUpravaFormy

    upraveneKrouzky.to_excel(config.dest_krouzky, index=False)

def stahni_obory_predmetu(df, katedra, semestr, rok):    
    for index, row in df.iterrows():
        if not(os.path.isfile(config.folder_predmetInfo +"predmet" + str(row["zkratka"]))):
            print("Zkratka= " + str(row["zkratka"]) + ", katedra = " + katedra +".")

            stag_vars = {
            "lang" : "cs",
            "outputFormat" : "CSV",
            "outputFormatEncoding" : "utf-8",
            "zkratka" : str(row["zkratka"]),
            "katedra" : katedra, 
            "rok" : rok
            }
            save_csv("https://ws.ujep.cz/ws/services/rest2/predmety/getOboryPredmetu", stag_vars, "predmet" + str(row["zkratka"]), config.folder_predmetInfo)   
