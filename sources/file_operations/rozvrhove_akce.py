
import os
import pandas as pd
import binpacking

import sources.config as config
import sources.global_functions as global_functions
import sources.stahovani as stahovani

# Projde dataframe, ke všem předmětům bez rozvrhovaných hodin
# napíše poznámku "Pouze AA" 
def najdi_aa_akce(df, katedra, semestr, rok):
    poznamky_list = [""] * len(df)
    for index, row in df.iterrows():
        if all(global_functions.bezpecna_int_konverze(row[col]) == 0 for col in ["jednotekPrednasek", "jednotekCviceni", "jednotekSeminare"]):
            poznamky_list[index] = "Pouze AA"

    df["Poznámky"] = poznamky_list
    return df

# Funkce přečte info o předmětu, nalezne počty studentů na jeho individuálních kroužcích
# a podle toho rozdělí přemět na minimum rozvrhových akcí. Kroužky s počtem studentů přesahujícím kapacitu se dělí na části.
# Dělí se na 3 bloky kódu podle typu akce.
# POZN. Hodnota "-121" která se občas v kódu objevuje, je zde kvůli tomu že se objevuje v dodaném souboru seznamu kroužků.
# Tvůrce seznamu toto číslo využíva namísto nuly pro označení prázdného kroužku. 
def rozdel_na_rozvrhove_akce(df, katedra, semestr, rok):
    df = najdi_aa_akce(df, katedra, semestr, rok)
    new_dataframe = []
    for index, row in df.iterrows():
        if((row["pocetStudentu"] > 0) & (row["Poznámky"] != "Pouze AA")):
            
            #prednasky
            if(int(row["jednotekPrednasek"]) > 0):
                if(row["jednotkaPrednasky"] == "HOD/TYD"):
                    prednaska_kapacita = config.prednaska_kapacita                    
                    if(os.path.isfile(config.dest_kapacity)):
                        df_kapacita = pd.read_excel(config.dest_kapacity, na_filter=False, dtype=str)
                        df_kapacita = df_kapacita[(df_kapacita['zkratka']==row['zkratka'])]
                        if not(df_kapacita.empty):
                            if(df_kapacita['prednaska'].values[0]!=''):
                                if(int(df_kapacita['prednaska'].values[0]) > 0):
                                    prednaska_kapacita = df_kapacita['prednaska'].values[0]
                    krouzky = row["krouzky"].split(",")
                    df_krouzky = pd.read_excel(config.dest_krouzky)
                    krouzek_studenti_nazvy = []
                    krouzek_studenti_pocty = []
                    for krouzek in krouzky:
                        found_krouzek = df_krouzky.loc[df_krouzky['Kód kroužku'] == krouzek]

                        if(found_krouzek["Počet studentů kroužku"].values[0] == -121):
                            continue
                        elif(found_krouzek["Počet studentů kroužku"].values[0] > prednaska_kapacita):
                            # pokud počet studentů kroužku přesahuje kapacitu,  rozdělím co nejvíce rovnoměrně na několik kroužků
                            pocet_dilcich_krouzku = global_functions.rozdel_na_cela_cisla(found_krouzek["Počet studentů kroužku"].values[0], prednaska_kapacita)
                            for index, krouzek_cast in enumerate(pocet_dilcich_krouzku):
                                krouzek_studenti_nazvy.append(str(found_krouzek["Kód kroužku"].values[0]) + "(" + str(index) + ")")
                                krouzek_studenti_pocty.append(int(krouzek_cast))

                        else:
                            krouzek_studenti_nazvy.append(str(found_krouzek["Kód kroužku"].values[0]))
                            krouzek_studenti_pocty.append(int(found_krouzek["Počet studentů kroužku"].values[0]))
                    krouzky_map = dict(zip(krouzek_studenti_nazvy,krouzek_studenti_pocty))
                    result=binpacking.to_constant_volume(krouzky_map, prednaska_kapacita)
                    for i in result:
                        studenti_count = 0
                        for j in i.values():
                            studenti_count = studenti_count + j
                        krouzkystr = ""
                        for a in i:
                            krouzkystr = krouzkystr + "," + str(a)
                        krouzkystr=krouzkystr[1:] #Odebere ',' na začátku seznamu kroužků
                        new_dataframe.append([row["zkratka"],row["nazevDlouhy"], row["prednasejiciSPodily"], " ", " ", row["jednotekPrednasek"], row["jednotkaPrednasky"], " ", " ", " ", " ", row["statut"], row["doporucenyRocnik"], row["doporucenySemestr"], krouzkystr, studenti_count, row["forma"], row["Poznámky"]])
                else:
                    new_dataframe.append([row["zkratka"],row["nazevDlouhy"], row["prednasejiciSPodily"], " ", " ", row["jednotekPrednasek"], row["jednotkaPrednasky"], " ", " ", " ", " ", row["statut"], row["doporucenyRocnik"], row["doporucenySemestr"], row["krouzky"], row["pocetStudentu"], row["forma"], row["Poznámky"]])
            
            #cviceni
            if(int(row["jednotekCviceni"]) > 0):
                if(row["jednotkaCviceni"] == "HOD/TYD"):
                    cviceni_kapacita = config.cviceni_kapacita
                    
                    if(os.path.isfile(config.dest_kapacity)):
                        df_kapacita = pd.read_excel(config.dest_kapacity, na_filter=False)
                        df_kapacita["zkratka"] = df_kapacita["zkratka"].astype(str)
                        df_kapacita = df_kapacita[(df_kapacita['zkratka']==row['zkratka'])]
                        if not(df_kapacita.empty):
                            if(int(df_kapacita['cviceni'].values[0]) > 0):
                                cviceni_kapacita = int(df_kapacita['cviceni'].values[0])
                    krouzky = row["krouzky"].split(",")
                    df_krouzky = pd.read_excel(config.dest_krouzky)
                    krouzek_studenti_nazvy = []
                    krouzek_studenti_pocty = []
                    for krouzek in krouzky:
                        found_krouzek = df_krouzky.loc[df_krouzky['Kód kroužku'] == krouzek]
                        if(found_krouzek["Počet studentů kroužku"].values[0] ==-121):
                            continue
                        elif(found_krouzek["Počet studentů kroužku"].values[0] > cviceni_kapacita):
                            pocet_dilcich_krouzku = global_functions.rozdel_na_cela_cisla(found_krouzek["Počet studentů kroužku"].values[0], cviceni_kapacita)
                            #print(pocet_dilcich_krouzku)
                            for index, krouzek_cast in enumerate(pocet_dilcich_krouzku):

                                krouzek_studenti_nazvy.append(str(found_krouzek["Kód kroužku"].values[0]) + "(" + str(index) + ")")
                                krouzek_studenti_pocty.append(int(krouzek_cast))
                        else:
                            krouzek_studenti_nazvy.append(str(found_krouzek["Kód kroužku"].values[0]))
                            krouzek_studenti_pocty.append(int(found_krouzek["Počet studentů kroužku"].values[0]))
                     
                    krouzky_map = dict(zip(krouzek_studenti_nazvy,krouzek_studenti_pocty))
                    result=binpacking.to_constant_volume(krouzky_map, cviceni_kapacita)
                    for i in result:
                        studenti_count = 0
                        for j in i.values():
                            studenti_count = studenti_count + j
                        krouzkystr = ""
                        for a in i:
                            krouzkystr = krouzkystr + "," + str(a)
                        krouzkystr=krouzkystr[1:]
                        new_dataframe.append([row["zkratka"],row["nazevDlouhy"], " ", row["cviciciSPodily"], " ", " ", " ", row["jednotekCviceni"], row["jednotkaCviceni"], " ", " ", row["statut"], row["doporucenyRocnik"], row["doporucenySemestr"], krouzkystr, studenti_count, row["forma"], row["Poznámky"]])
                else:
                    
                    new_dataframe.append([row["zkratka"],row["nazevDlouhy"], " ", row["cviciciSPodily"], " ", " ", " ", row["jednotekCviceni"], row["jednotkaCviceni"], " ", " ", row["statut"], row["doporucenyRocnik"], row["doporucenySemestr"], row["krouzky"], row["pocetStudentu"], row["forma"], row["Poznámky"]])
            
            #seminare
            if(int(row["jednotekSeminare"]) > 0):
                if(row["jednotkaSeminare"] == "HOD/TYD"):
                    krouzky = row["krouzky"].split(",")
                    df_krouzky = pd.read_excel(config.dest_krouzky)
                    seminar_kapacita = config.seminar_kapacita
                    if(os.path.isfile(config.dest_kapacity)):
                        df_kapacita = pd.read_excel(config.dest_kapacity, na_filter=False)
                        df_kapacita["zkratka"] = df_kapacita["zkratka"].astype(str)
                        df_kapacita = df_kapacita[(df_kapacita['zkratka']==row['zkratka'])]
                        if not(df_kapacita.empty):
                            if(int(df_kapacita['seminar'].values[0]) > 0):
                                seminar_kapacita = int(df_kapacita['seminar'].values[0])
                    krouzek_studenti_nazvy = []
                    krouzek_studenti_pocty = []
                    for krouzek in krouzky:
                        found_krouzek = df_krouzky.loc[df_krouzky['Kód kroužku'] == krouzek]                    
                        if(found_krouzek["Počet studentů kroužku"].values[0] ==-121):
                            continue
                        elif(found_krouzek["Počet studentů kroužku"].values[0] > seminar_kapacita):
                            pocet_dilcich_krouzku = global_functions.rozdel_na_cela_cisla(found_krouzek["Počet studentů kroužku"].values[0], seminar_kapacita)
                            for index, krouzek_cast in enumerate(pocet_dilcich_krouzku):
                                krouzek_studenti_nazvy.append(str(found_krouzek["Kód kroužku"].values[0]) + "(" + str(index) + ")")
                                krouzek_studenti_pocty.append(int(krouzek_cast))
                        else:
                            krouzek_studenti_nazvy.append(str(found_krouzek["Kód kroužku"].values[0]))
                            krouzek_studenti_pocty.append(int(found_krouzek["Počet studentů kroužku"].values[0]))
                    krouzky_map = dict(zip(krouzek_studenti_nazvy,krouzek_studenti_pocty))
                    result=binpacking.to_constant_volume(krouzky_map, seminar_kapacita)
                    for i in result:
                        studenti_count = 0
                        for j in i.values():
                            studenti_count = studenti_count + j
                        krouzkystr = ""
                        for a in i:
                            krouzkystr = krouzkystr + "," + str(a)
                        krouzkystr=krouzkystr[1:]
                        new_dataframe.append([row["zkratka"],row["nazevDlouhy"], " ", " ", row["seminariciSPodily"], " ", " ", " ", " ", row["jednotekSeminare"], row["jednotkaSeminare"], row["statut"], row["doporucenyRocnik"], row["doporucenySemestr"], krouzkystr, studenti_count, row["forma"], row["Poznámky"]])
                else:
                    new_dataframe.append([row["zkratka"],row["nazevDlouhy"], " ", " ", row["seminariciSPodily"], " ", " ", " ", " ", row["jednotekSeminare"], row["jednotkaSeminare"], row["statut"], row["doporucenyRocnik"], row["doporucenySemestr"], row["krouzky"], row["pocetStudentu"], row["forma"], row["Poznámky"]])

        else:
            new_dataframe.append([row["zkratka"],row["nazevDlouhy"], row["prednasejiciSPodily"], row["cviciciSPodily"], row["seminariciSPodily"], row["jednotekPrednasek"], row["jednotkaPrednasky"], row["jednotekCviceni"], row["jednotkaCviceni"], row["jednotekSeminare"], row["jednotkaSeminare"], row["statut"], row["doporucenyRocnik"], row["doporucenySemestr"], row["krouzky"], row["pocetStudentu"], row["forma"], row["Poznámky"]])
    new_df = pd.DataFrame(new_dataframe, columns=["zkratka","nazevDlouhy","prednasejiciSPodily","cviciciSPodily","seminariciSPodily","jednotekPrednasek","jednotkaPrednasky","jednotekCviceni","jednotkaCviceni","jednotekSeminare","jednotkaSeminare","statut","doporucenyRocnik","doporucenySemestr","krouzky","pocetStudentu","forma","Poznámky"])
    return new_df

# Stáhne rozvrh katedry v minulém roce, pomocí několika kritérii
# (Stejná místnost, stejný den, stejný začátek a konec apod.)
# najde všechny množiny společné výuky, které pak vrací volající funkci.
def hledani_spol_vyuky(katedra, semestr, rok):
    if not(os.path.isfile(global_functions.getRozvrhKatedry(katedra, semestr, rok))):
        stahovani.stahni_rozvrh_katedry(katedra,semestr,rok)
    df = pd.read_csv(global_functions.getRozvrhKatedry(katedra, semestr, rok), usecols = ['predmet','budova','mistnost','typAkceZkr','denZkr','hodinaSkutOd','hodinaSkutDo','tydenOd','tydenDo', 'tydenZkr'], sep=config.separator, engine='python', keep_default_na=False)
    df = df[df.denZkr != ""] #odebráni nerozvrhovaných akcí
    df_paralelni = df[df.duplicated(subset=['budova','mistnost','denZkr','hodinaSkutOd','hodinaSkutDo','tydenOd','tydenDo', 'tydenZkr'], keep=False)]
    df_paralelni = df_paralelni.groupby(['budova','mistnost','denZkr','hodinaSkutOd','hodinaSkutDo','tydenOd','tydenDo', 'tydenZkr'])
    spol_vyuka = []
    for k, g in df_paralelni:   
        temp_row = ""
        for row in g.itertuples():  
            if(temp_row==""):
                temp_row = str(row.predmet)
            else:
                temp_row = temp_row + "," + str(row.predmet)   

        spol_vyuka.append(temp_row)

    #Odstranění společné výuky dvou předmětů v několika akcích
    spol_vyuka = list(dict.fromkeys(spol_vyuka))

    return spol_vyuka  