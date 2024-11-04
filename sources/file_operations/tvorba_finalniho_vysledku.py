
import pandas as pd
import re
import sources.config as config
import sources.file_operations.rozvrhove_akce as ra
import sources.global_functions as global_functions

#Složí jméno vyučujícího i s tituly z několika sloupců do jednoho stringu 
def sloz_jmeno_ucitele(df):
    jmeno = ""
    if(isinstance(df, pd.DataFrame)):
        if(df['titulPred.ucitel'].values[0] != ""):
            jmeno = jmeno + df['titulPred.ucitel'].values[0] + " "
        jmeno = jmeno + df["jmeno.ucitel"].values[0] + " " + df["prijmeni.ucitel"].values[0]
        if(df["titulZa.ucitel"].values[0] != ""):
            jmeno = jmeno + ", " + df["titulZa.ucitel"].values[0]
    else:
        if(df['titulPred.ucitel'] != ""):
            jmeno = jmeno + df['titulPred.ucitel'] + " "
        jmeno = jmeno + df["jmeno.ucitel"] + " " + df["prijmeni.ucitel"]
        if(df["titulZa.ucitel"] != ""):
            jmeno = jmeno + ", " + df["titulZa.ucitel"]

    return jmeno

# Zapíše vyučující do seznamu, vypočítá hodinovou zátěž z jim přiřazených RA.
# Bere v potaz společnou výuku, jejichž trvání přičítá jednou.
# Pokud má společnou výuku rozvrhových akcí s jiným počtem hodin,
# přiřazuje se ta vyšší.
def pricti_zatez(line1, jednotka_hodin, vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS,vyucujici_zatez_MIX, typ, forma):    
    match(typ):
        case "Př":
            sloupec1='prednasejiciSPodily'
            sloupec2='jednotekPrednasek'
        case "Cv":
            sloupec1='cviciciSPodily'
            sloupec2='jednotekCviceni'
        case "Se":
            sloupec1='seminariciSPodily'
            sloupec2='jednotekSeminare'
    
    vyucujici = str(line1['zvolenyVyucujici'])
    if(jednotka_hodin=='HOD/SEM'):
        hodiny_k_pricteni = round(float(line1[sloupec2]) / 13, 2)
    else:
        hodiny_k_pricteni = float(line1[sloupec2])
    if(vyucujici==' '):
        print("ERROR: nalezen prazdny vyucujici")
    elif vyucujici in vyucujici_jmeno:
        index = vyucujici_jmeno.index(vyucujici)
        if not(isinstance(line1['spolecnaVyuka'],int)):
            match(forma):
                case "Prezenční":
                    vyucujici_zatez_PS[index] = float(vyucujici_zatez_PS[index]) + hodiny_k_pricteni
                case "Kombinovaná":
                    vyucujici_zatez_KS[index] = float(vyucujici_zatez_KS[index]) + hodiny_k_pricteni
                case "Mix":
                    vyucujici_zatez_MIX[index] = float(vyucujici_zatez_MIX[index]) + hodiny_k_pricteni
    else:
        vyucujici_jmeno.append(vyucujici)
        if not(isinstance(line1['spolecnaVyuka'],int)):
            match(forma):
                case "Prezenční":
                    vyucujici_zatez_PS.append(hodiny_k_pricteni)
                    vyucujici_zatez_KS.append(0)
                    vyucujici_zatez_MIX.append(0)

                case "Kombinovaná":
                    vyucujici_zatez_PS.append(0)
                    vyucujici_zatez_KS.append(hodiny_k_pricteni)
                    vyucujici_zatez_MIX.append(0)

                case "Mix":
                    vyucujici_zatez_PS.append(0)
                    vyucujici_zatez_KS.append(0)
                    vyucujici_zatez_MIX.append(hodiny_k_pricteni)
        else:
                    vyucujici_zatez_PS.append(0)
                    vyucujici_zatez_KS.append(0)
                    vyucujici_zatez_MIX.append(0)
        vyucujici_paralelVyukaKody.append("")

def rozdel_vysledny_soubor(df, katedra, semestr, rok):
    spolecne_predmety_column = [" "] * len(df)
    predmety_jsou_mix_column = ["0"] * len(df) #Pokud společná výuka zahrnuje předměty, které mají rozdílnou formu, jejich forma je pomocí tohoto pole v pozdějším kroku přepsána na Mix
     
    spol_vyuka = ra.hledani_spol_vyuky(katedra, semestr, int(rok)-1)
    paralel_int = 0
    df['zkratka'] = df.zkratka.astype(str)

    for paralelni_set in spol_vyuka:
        typ = paralelni_set[:2]
        kody = paralelni_set[4:].split(",")
        lever = 0 # určuje jestli se má v loopu pokračovat
        for kod in kody: #pokud v setu paralelni vyuky jsou mene nez 2 predmety ktere jsou i v hledanem roce, ignoruj set
            if (str(kod) in df['zkratka'].values):
                lever +=1
        # TODO Kontrola nejen toho jestli jsou vsechny kody v seznamu, ale jestli odpovida jejich typ (pr, cv, se)
        if(lever>=2):
            lever = 0
            for kod in kody:
                df_spolecna_vyuka = df.loc[df['zkratka'] == kod]
                if not df_spolecna_vyuka.empty:
                    match(typ):
                        case "Př":
                            if not(str(df_spolecna_vyuka['jednotekPrednasek'].unique()) == "[' ' 0]"):
                                lever+=1
                        case "Cv":
                            if not(str(df_spolecna_vyuka['jednotekCviceni'].unique()) == "[' ' 0]"):
                                lever+=1
                        case "Se":
                            if not(str(df_spolecna_vyuka['jednotekSeminare'].unique()) == "[' ' 0]"):
                                lever+=1
                        case _:
                            print("Problem s kodem paralelni vyuky")
                            exit()
        else:
            lever = 0

        
        if(lever>=2):
            pridany_kod_lever = 0
            predchozi_forma = "" # Pro kontrolu, jestli jsou vsechny formy (prezencni, kombinovane, mix) stejne 
            for kod in kody:
                #for index, row in df.iterrows(): 
                df_spol_vyuka_slice = df[df['zkratka'].isin(kody)]#TODO delat lepe, iterace asi neni nutna 
                for index, row in df_spol_vyuka_slice.iterrows(): 
                    if(row['zkratka'] == str(kod)):
                        #Kontrola, jestli je nutné přesunout předměty spol. výuky do MIX
                        print("Index: " + str(index))
                        print("Par. kod: " + str(paralel_int))
                        print("predchozi_forma: " + predchozi_forma)
                        print("Forma na radku: " + row["forma"])

                        if(predchozi_forma==""):
                            predchozi_forma=row["forma"]
                        elif(row["forma"]!=predchozi_forma):
                            print("elif dosazen u predmetu: " + row['zkratka'] + " v indexu: " + str(index))
                            df.loc[df_spol_vyuka_slice.index, 'forma'] = 'Mix'
                            predchozi_forma='Mix'
                        match(typ):
                            case "Př":
                                if(row['jednotekPrednasek'].isnumeric()):
                                    if not(bool(re.search(r'\d', str(spolecne_predmety_column[index])))):
                                        spolecne_predmety_column[index] = paralel_int
                                    else:
                                        spolecne_predmety_column[index] = str(spolecne_predmety_column[index]) + "," + str(paralel_int)
                                    pridany_kod_lever=pridany_kod_lever + 1
                                    #print("Predmet nalezen na indexu: " + str(index) + " , prirazen identifikator " + str(paralel_int))
                                    break
                            case "Cv":
                                if(row['jednotekCviceni'].isnumeric()):
                                    if not(bool(re.search(r'\d', str(spolecne_predmety_column[index])))):
                                        spolecne_predmety_column[index] = paralel_int
                                    else:
                                        spolecne_predmety_column[index] = str(spolecne_predmety_column[index]) + "," + str(paralel_int)
                                    pridany_kod_lever=pridany_kod_lever + 1
                                    #print("Predmet nalezen na indexu: " + str(index) + " , prirazen identifikator " + str(paralel_int))
                                    break
                            case "Se":
                                if(row['jednotekSeminare'].isnumeric()):
                                    if not(bool(re.search(r'\d', str(spolecne_predmety_column[index])))):
                                        spolecne_predmety_column[index] = paralel_int
                                    else:
                                        spolecne_predmety_column[index] = str(spolecne_predmety_column[index]) + "," + str(paralel_int)
                                    pridany_kod_lever=pridany_kod_lever + 1
                                    #print("Predmet nalezen na indexu: " + str(index) + " , prirazen identifikator " + str(paralel_int))
                                    break
                            case _:
                                print("Problem s kodem paralelni vyuky")
                                exit()


            if(pridany_kod_lever>=2):
                print("Pridany kod lever: " + str(pridany_kod_lever), "paralel int: " + str(paralel_int))
                paralel_int += 1    
    df['spolecnaVyuka'] = spolecne_predmety_column
    df['forma'] = df['forma'].combine_first(pd.Series(predmety_jsou_mix_column))
    print(df['forma'])


    #print(spolecne_predmety_column)

            
    #hledani vyucujicich pro RA dle min. roku
    vyucujici_akce = [' '] * len(df)
    vyucujici_min_rok = [' '] * len(df)
    vyucujici_zdroj = [' '] * len(df)
    df_minRok = pd.read_csv(global_functions.getRozvrhKatedry(katedra, semestr, int(rok) -1),sep=config.separator, engine='python', keep_default_na=False, dtype=str)
    #df_minRok['predmet'] = df_minRok.predmet.astype(str)
    # předměty u kterých platí že 1přednáška/cvičení/seminář = 1 RA
    df_slice = df.drop_duplicates(['zkratka','prednasejiciSPodily','cviciciSPodily','seminariciSPodily'])
    df_slice['pocetStudentu'] = df_slice.pocetStudentu.astype(int)
    df_slice = df_slice[(df_slice['pocetStudentu'] > 0)]
    df_slice = df_slice[(df_slice['Poznámky'] != "Pouze AA")]
    blacklist = []
    for vyucindex, vyucrow in df_slice.iterrows():
        blacklist.append(vyucindex)
        df_minRok_slice = df_minRok[(df_minRok['predmet']==vyucrow['zkratka'])]
        if not (df_minRok_slice.empty):
            df_minRok_slice = df_minRok_slice[(df_minRok_slice['typAkceZkr']==global_functions.ziskej_typ_RA(vyucrow))] 
            if not (df_minRok_slice.empty):
                vyucujici_akce[vyucindex] = sloz_jmeno_ucitele(df_minRok_slice)
                vyucujici_min_rok[vyucindex] = sloz_jmeno_ucitele(df_minRok_slice)
            else:
                #pridej prvniho vyucujiciho z seznamu, pokud tam nejaky je
                if(global_functions.ziskej_prvni_vyucujici(vyucrow,global_functions.ziskej_typ_RA(vyucrow))!="nan" ):
                    vyucujici_akce[vyucindex] = global_functions.ziskej_prvni_vyucujici(vyucrow,global_functions.ziskej_typ_RA(vyucrow))
                pass
        else:
            #pridej prvniho vyucujiciho z seznamu, pokud tam nejaky je
            if(global_functions.ziskej_prvni_vyucujici(vyucrow,global_functions.ziskej_typ_RA(vyucrow))!="nan"):
                vyucujici_akce[vyucindex] = global_functions.ziskej_prvni_vyucujici(vyucrow,global_functions.ziskej_typ_RA(vyucrow))
            pass
    #předměty s typem jejichž výuka je rozdělená na více RA
    df_slice = df.loc[~df.index.isin(blacklist)]
    df_slice['pocetStudentu'] = df_slice.pocetStudentu.astype(int)
    df_slice = df_slice[(df_slice['pocetStudentu'] > 0)]
    df_slice = df_slice[(df_slice['Poznámky'] != "Pouze AA")]
    list_zkratky = df['zkratka'].to_list()
    list_zkratky = list(dict.fromkeys(list_zkratky))
    for zkratka in list_zkratky:
        for i in range(3):
            match i:
                case 0:
                    vyucujici_sloupec='prednasejiciSPodily'
                    typ = 'Př'
                case 1:
                    vyucujici_sloupec='cviciciSPodily'
                    typ = 'Cv'
                case 2:
                    vyucujici_sloupec='seminariciSPodily'
                    typ = 'Se'                      
            df_slice_temp = df_slice[(df_slice[vyucujici_sloupec]!=' ') & (df_slice['zkratka']==zkratka)]
            if not(df_slice_temp.empty):
                df_minRok_slice = df_minRok[(df_minRok['predmet']==str(zkratka))&(df_minRok['typAkceZkr']==typ)]
                if not(df_minRok_slice.empty):
                    
                    vyucujici_list_temp = []
                    for index, row in df_minRok_slice.iterrows():
                        vyucujici_list_temp.append(sloz_jmeno_ucitele(row))
                    vyucujici_list_temp.pop(0)

                    for jmeno in vyucujici_list_temp:
                        if(jmeno==''):
                            print("ERROR: spatne nacitani jmen vyucujicich z min.roku")
                            print(vyucujici_list_temp)
                            print("Delka hledaneho slice je " + str(len(df_slice_temp)))
                            print("Delka minuleho slice je " + str(len(vyucujici_list_temp)))
                            print(df_slice_temp)

                            exit()

                    while(len(vyucujici_list_temp) < len(df_slice_temp)):
                        vyucujici_list_temp.append(' ')
                    if(len(vyucujici_list_temp) > len(df_slice_temp)):
                        a = len(vyucujici_list_temp) - len(df_slice_temp)
                        del vyucujici_list_temp[-a]

                    vyucujici_iterator = 0
                    for index, row in df_slice_temp.iterrows():
                        if((vyucujici_list_temp[vyucujici_iterator]==' ') & (global_functions.ziskej_prvni_vyucujici(df_slice_temp.iloc[0], typ)!="nan") & (global_functions.ziskej_prvni_vyucujici(df_slice_temp.iloc[0], typ)!=" ") & (global_functions.ziskej_prvni_vyucujici(df_slice_temp.iloc[0], typ)!="") & (global_functions.ziskej_prvni_vyucujici(df_slice_temp.iloc[0], typ)!=" ") ):
                            vyucujici_akce[index] = global_functions.ziskej_prvni_vyucujici(df_slice_temp.iloc[0], typ)
                            vyucujici_min_rok[index] = ' '
                            vyucujici_zdroj[index] = "B. Vyučující dosazen první ze seznamu"
                        elif((vyucujici_list_temp[vyucujici_iterator]!=' ')):
                            vyucujici_akce[index] = vyucujici_list_temp[vyucujici_iterator]
                            vyucujici_min_rok[index] = vyucujici_list_temp[vyucujici_iterator]
                            vyucujici_zdroj[index] = "A. Převzatý z minulého roku"
                        else:
                            pass
                        vyucujici_iterator += 1         


    df['zvolenyVyucujici'] = vyucujici_akce
    df['predeslyVyucujici'] = vyucujici_min_rok
    for index, i in enumerate(vyucujici_akce):
        if(vyucujici_zdroj[index]==' '):
            if(str(i) != ' '):
                if(str(i)==str(vyucujici_min_rok[index])):
                    vyucujici_zdroj[index] = "A. Převzatý z minulého roku"
                else:
                    vyucujici_zdroj[index] = "B. Vyučující dosazen první ze seznamu"
            else:
                vyucujici_zdroj[index] = "C. Vyučující nedosazen"
    df['zdrojVyucujiciho'] = vyucujici_zdroj

    #zatez vyucujicich - pouze neparalelne vyucovane predmety
    vyucujici_jmeno = []
    vyucujici_paralelVyukaKody = []
    vyucujici_zatez_PS = []
    vyucujici_zatez_KS = []
    vyucujici_zatez_MIX = []
    for iterator1, line1 in df.iterrows():
        if((line1["Poznámky"] != "Pouze AA") & (line1['pocetStudentu']!=0)):
            if(line1['forma']=="Prezenční"):
                if ((line1['jednotkaPrednasky'] == "HOD/SEM") | (line1['jednotkaPrednasky'] == "HOD/TYD")):
                    if(int(line1['jednotekPrednasek'])>0):
                        pricti_zatez(line1, line1['jednotkaPrednasky'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Př", "Prezenční")


                if ((line1['jednotkaCviceni'] == "HOD/SEM") | (line1['jednotkaCviceni'] == "HOD/TYD")):
                    if(int(line1['jednotekCviceni'])>0):
                        pricti_zatez(line1, line1['jednotkaCviceni'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Cv", "Prezenční")


                if ((line1['jednotkaSeminare'] == "HOD/SEM") | (line1['jednotkaSeminare'] == "HOD/TYD")):
                    if(int(line1['jednotekSeminare'])>0):
                        pricti_zatez(line1, line1['jednotkaSeminare'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Se", "Prezenční")
            if(line1['forma']=="Kombinovaná"):
                if ((line1['jednotkaPrednasky'] == "HOD/SEM") | (line1['jednotkaPrednasky'] == "HOD/TYD")):
                    if(int(line1['jednotekPrednasek'])>0):
                        pricti_zatez(line1, line1['jednotkaPrednasky'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Př", "Kombinovaná")


                if ((line1['jednotkaCviceni'] == "HOD/SEM") | (line1['jednotkaCviceni'] == "HOD/TYD")):
                    if(int(line1['jednotekCviceni'])>0):
                        pricti_zatez(line1, line1['jednotkaCviceni'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Cv", "Kombinovaná")

                if ((line1['jednotkaSeminare'] == "HOD/SEM") | (line1['jednotkaSeminare'] == "HOD/TYD")):
                    if(int(line1['jednotekSeminare'])>0):
                        pricti_zatez(line1, line1['jednotkaSeminare'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Se", "Kombinovaná")

            if(line1['forma']=="Mix"):
                if ((line1['jednotkaPrednasky'] == "HOD/SEM") | (line1['jednotkaPrednasky'] == "HOD/TYD")):
                    if(int(line1['jednotekPrednasek'])>0):
                        pricti_zatez(line1, line1['jednotkaPrednasky'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Př", "Mix")
                
                if ((line1['jednotkaCviceni'] == "HOD/SEM") | (line1['jednotkaCviceni'] == "HOD/TYD")):
                    if(int(line1['jednotekCviceni'])>0):
                        pricti_zatez(line1, line1['jednotkaCviceni'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Cv", "Mix")

                if ((line1['jednotkaSeminare'] == "HOD/SEM") | (line1['jednotkaSeminare'] == "HOD/TYD")):
                    if(int(line1['jednotekSeminare'])>0):
                        pricti_zatez(line1, line1['jednotkaSeminare'], vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS, vyucujici_zatez_MIX, "Se", "Mix")

    #zatez vyucujicich - pouze paralelni predmety
    spolecne_predmety_column_str = [ str(x) for x in spolecne_predmety_column if x is not ' ' ]

    #prevedeni string listu na integery
    spolecne_predmety_column = []
    for radek in spolecne_predmety_column_str:
        split_items = radek.split(',')
        spolecne_predmety_column.extend([int(i) if i.isdigit() else float(i) for i in split_items])
    print(spolecne_predmety_column)
    if(spolecne_predmety_column):
        print("i (max): " + str(max(spolecne_predmety_column)))
        for i in range(max(spolecne_predmety_column)+1):
            df_paralelPredmety = df[df['spolecnaVyuka'].astype(str).apply(lambda x: str(i) in x.split(','))]
            if(df_paralelPredmety.empty):
                continue
            print("i (" + str(i) + ") je nalezeno v seznamu cisel spol. vyuky.")
            sloupec = 'zvolenyVyucujici'

            if not(df_paralelPredmety['jednotekPrednasek'].iloc[0] == " "):
                df_paralelPredmety['jednotekPrednasek'] = pd.to_numeric(df_paralelPredmety['jednotekPrednasek'], errors='coerce')
                hodiny = df_paralelPredmety['jednotekPrednasek'].max()
            elif not(df_paralelPredmety['jednotekCviceni'].iloc[0] == " "):
                df_paralelPredmety['jednotekCviceni'] = pd.to_numeric(df_paralelPredmety['jednotekCviceni'], errors='coerce')
                hodiny = df_paralelPredmety['jednotekCviceni'].max()
            elif not(df_paralelPredmety['jednotekSeminare'].iloc[0] == " "):
                df_paralelPredmety['jednotekSeminare'] = pd.to_numeric(df_paralelPredmety['jednotekSeminare'], errors='coerce')
                hodiny = df_paralelPredmety['jednotekSeminare'].max()
            vyucujici = df_paralelPredmety[sloupec].iloc[0]
            if(vyucujici in vyucujici_jmeno):
                index = vyucujici_jmeno.index(vyucujici)
                match(df_paralelPredmety['forma'].iloc[0]):
                    case "Prezenční":
                        vyucujici_zatez_PS[index] = float(vyucujici_zatez_PS[index]) + hodiny
                    case "Kombinovaná":
                        vyucujici_zatez_KS[index] = float(vyucujici_zatez_KS[index]) + hodiny
                    case "Mix":
                        vyucujici_zatez_MIX[index] = float(vyucujici_zatez_MIX[index]) + hodiny

                vyucujici_paralelVyukaKody[index] = vyucujici_paralelVyukaKody[index] + "|" + str(i) + "|"
            else:
                print("Potencialni problem s paralel vyukou - vyucujici nenalezen")

    new_dataframe = []
    for idx, x in enumerate(vyucujici_jmeno):
        if (x != "nan"):
            new_dataframe.append([x, vyucujici_zatez_PS[idx], vyucujici_zatez_KS[idx], vyucujici_zatez_MIX[idx], vyucujici_paralelVyukaKody[idx]])
    
    #zkontroluj jestli je někde předmět který má studenty ale nemá zvoleného vyučujícího
    chybejici_vyucujici_check = df[(~df['Poznámky'].str.contains("Pouze AA")) & 
                                (df['pocetStudentu'] != "0") & 
                                (df['zdrojVyucujiciho']=="C. Vyučující nedosazen")]
    if not(chybejici_vyucujici_check.empty):
        df.loc[chybejici_vyucujici_check.index, 'Poznámky'] = 'VAROVÁNÍ: Chybí vyučující akce.'

    #odeber sloupce o seminarich, pokud ve vysledku zadny neni
    seminar_check = df['jednotekSeminare'].unique()

    if(str(seminar_check) == "[\' \' \'0\']"):
        del df['jednotekSeminare']
        del df['jednotkaSeminare']
        del df['seminariciSPodily']

    #Odebrání dalších sloupců pokud jsou prázdné nebo pro uživatele nepotřebné
    poznamky_check = df["Poznámky"].unique()
    if(str(poznamky_check) == "[nan]"):
        print("Poznámky check prošel, sloupec se maže...")
        #exit()
        del df["Poznámky"] 
    del df['doporucenySemestr']
    del df['statut']

    #Tvorba sloupce s počtem kroužků
    df['krouzky'] = df['krouzky'].fillna("")
    df['krouzky'] = df['krouzky'].astype(str)
    df['pocetKrouzku'] = df['krouzky'].apply(lambda krouzky: krouzky.count('.'))
    # Odebrání nevyužitých sloupců z dataframu
    columns_list = ['zkratka', 'nazevDlouhy', 'prednasejiciSPodily', 'cviciciSPodily']
    if 'jednotekSeminare' in df:
        columns_list.extend(['seminariciSPodily'])
    columns_list.extend(['jednotekPrednasek', 'jednotkaPrednasky', 'jednotekCviceni', 'jednotkaCviceni'])
    if 'jednotekSeminare' in df:
        columns_list.extend(['jednotekSeminare', 'jednotkaSeminare'])
    columns_list.extend(['doporucenyRocnik', 'krouzky', 'pocetKrouzku', 'pocetStudentu', 'forma', 'spolecnaVyuka', 'zvolenyVyucujici', 'predeslyVyucujici', 'zdrojVyucujiciho'])
    if 'Poznámky' in df:
        columns_list.extend(['Poznámky'])

    df = df[columns_list]

    result_ZATEZ = pd.DataFrame(new_dataframe, columns=["vyucujiciJmeno","hodinyPS","hodinyKS","hodinyMIX","paralelniKody"]).astype({
        'vyucujiciJmeno' : 'string',
        'hodinyPS' : 'float',
        'hodinyKS' : 'float',
        'hodinyMIX' : 'float',
        'paralelniKody' : 'string',
    })
    # Finální úpravy dataframu, zápis do .xlsx souboru který je zobrazen uživateli.
    writer = pd.ExcelWriter(global_functions.getVysledekKatedry(katedra, semestr, rok), engine='xlsxwriter')
    result_PS = df[df["forma"] == 'Prezenční']
    result_KS = df[df["forma"] == 'Kombinovaná']
    result_MIX = df[df["forma"] == 'Mix']
    result_PS = result_PS.drop(["forma"], axis=1)
    result_KS = result_KS.drop(["forma"], axis=1)
    result_MIX = result_MIX.drop(["forma"], axis=1)
    result_PS.to_excel(writer, sheet_name='prezencni', index=False)
    result_KS.to_excel(writer, sheet_name='kombinovana', index=False)
    result_MIX.to_excel(writer, sheet_name='mix', index=False)
    result_ZATEZ.to_excel(writer, sheet_name='zatez', index=False)
    writer.close()  