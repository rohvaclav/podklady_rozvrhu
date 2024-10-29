import os
import sys

# URL pro případ problémů přihlášení:
#http://localhost:8501/?stagUserTicket=ticket&stagUserName=user&stagUserRole=ST&stagUserInfo=userinfo%3d
#(Generace nebude fungovat, slouží pouze k procházení předchozích výsledků)

# Nastavení - defaultní hodnoty na webovém rozhraní
prednaska_kapacita = 9999
cviceni_kapacita = 30
seminar_kapacita = 30

# Nastavení - komunikace se systémem IS STAG
separator=';' # pro čtení stažených tabulkových souborů
krouzky_rezim = "ze_souboru" # "stahovani": načítá seznam kroužků ze STAGu, momentálně nefunkční 
                             # "ze_souboru": pracuje s manuálně přiloženým souborem se seznamem kroužků


folder_local = os.path.dirname(os.path.abspath(sys.argv[0]))
folder = folder_local + "/sourcefiles/"
folder_programy = folder + "/programy/"
folder_obory = folder + "/obory/"
folder_predmety = folder + "/predmety/"
folder_vysledky = folder + "/vysledky/"
folder_predmetInfo = folder + "/predmetInfo/"
folder_ucitele = folder + "/ucitele/"
folder_rozvrhy = folder + "/rozvrhy/"
dest_krouzky = folder + "krouzky.xlsx"
dest_kapacity = folder + "kapacity.xlsx"
dest_pocty = folder + "pocty.xlsx"
vysledny_soubor= folder_local+"/vysledek.xlsx"

