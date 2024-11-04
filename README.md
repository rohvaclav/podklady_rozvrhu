# Základní popis

Aplikace slouží k vygenerováním podkladů pro tvorbu rozvrhu na Univerzitě Jana Evangelisty Purkyně v Ústí nad Labem (dále jen UJEP). Pomocí jednoduchého webového rozhraní může uživatel získat výstupní soubor se seznamem rozvrhových akcí pro zvolenou katedru, semestr a rok. 

# Jak začít

Ke spuštění aplikace je pro koncové uživatele nutné vytvořit soubor podklady_rozvrhu.exe pomocí PyInstaller. 
Alternativně lze vytvořit Docker soubor nebo manuálně připravit prostředí - v takovém případě se aplikace spouští příkazem `streamlit run main.py`

POZOR: Pro fungování aplikace je nutný soubor se seznamem kroužků, který je s ohledem na obsah soukromých dat dodáván pouze kvalifikovaným osobám členy rozvrhové komise UJEP.

# Obecná struktura
Tato aplikace je vyvinutá pouze v jazyce Python a funguje jen na straně klienta. Veškerá funkcionalita pro komunikaci s API IS STAG existuje pouze pro získání souborů, které jsou dále zpracovány lokálně. Před vysvětlením kódu je nutné brát v potaz, že k jeho funkci jsou potřeba mimo kódu dva tabulkové soubory. První je seznam kroužků, který je vytvářen členem rozvrhové komise. Druhým je nevyplněný vzorový soubor pro individuální zvolení kapacit pro předměty. Oba dva tyto soubory jsou dodávány společně s aplikací.

![Struktura adresáře](struktura_kod.png)

V adresáři aplikace je nejprve modul main.py, který inicializuje aplikaci a zároveň obsahuje implementaci Streamlitu. Tato knihovna  zprostředkovává webové rozhraní, skrze které uživatel interaguje s aplikací. 

Zároveň modul zahrnuje implementaci obnovování seznamu předmětů podle akademického roku. Využívá k tomu několik funkcí z ostatních modulů popsaných níže. Obecný postup tohoto procesu lze vidět na Obr. \ref{fig:Diagram_tvorby_seznamu_predmetu_na_rok}.

Mimo tohoto bloku kódu modul zprostředkovává vstupy uživatele v podobě textových polí, rozbalovacích nabídek a polí k nahrání souborů. Uživatel potom spouští program a stahuje soubory prostřednictvím tlačítek.

Na konci kódu a ve spodní části aplikace je poté implementace zobrazení výsledného podkladu k tvorbě rozvrhů v podobě tabulky přímo na stránce. Stejně jako samotný výstupní soubor má tabulka stejné listy mezi kterými lze přepínat. Avšak je zde nutné zmínit, že kvůli přehlednosti je tato tabulka omezená, tzn. nezobrazuje všechny sloupce, a je proto určená pouze jako náhled.

Struktura aplikace se dělí na dva podadresáře. Prvním je sourcefiles, který obsahuje veškeré soubory se kterými aplikace pracuje. nejpodstatnější jsou soubory ve formátu "slozenyVysledek[ROK].xlsx", které obsahují seznam všech platných předmětů pro daný akademický rok. Tento soubor slouží jako startovní bod pro tvorbu podkladů rozvrhu. Dále je jeho součástí soubor "krouzky.xlsx", což je předem zmíněný seznam kroužků. 

Součástí je i několik podadresářů které obsahují výsledky funkcí v modulu "stahovani.py", popsaném níže.

Druhým podadresářem je sources, který nejprve obsahuje několik menších modulů s obecnými funkcemi + nastavením aplikace, a složka file_operations, která zahrnuje větší moduly s hlavní funkcionalitou aplikace.

# Moduly

## main.py

Vstupní modul. Obsahuje streamlit rozhraní prostřednictvím kterého uživatel ovládá aplikaci. Uvnitř funkce `main` je zároveň volání několika funkcí pro obnovu seznamu předmětů a tvorbu výsledné podkladové tabulky, spojené s jejich tlačítky.
Dále zahrnuje funkce `get_user_ticket()`, která vrací ticket uživatele a `refresh_url()`, která obnoví stránku. Nakonec funkci `getKatedraList(rok)`, která pomocí zadaného roku zobrazí uvnitř rozbalovacího menu v prohlížeči katedry, které mají v tomto roce předměty.

## config.py: 
Obsahuje nastavení defaultních hodnot ve webovém rozhraní, zvolení některých proměnných použitých pro nastavení běhu programu a strukturu adresářů

## global_functions.py: 
Zahrnuje několik jednoduchých funkcí použitých napříč aplikací. Patří sem například převedení stringu "Prezenční" na "PS" prostřednictvím funkce `prepis_formu(x)`, nebo ošetřené čtení čísla ze stringu pomocí `bezpecna_int_konverze(value)`.

## setup.py: 
Velmi krátký modul který pomocí dat v config.py vytváří adresářovou strukturu.

## stahovani.py: 
Zajišťuje veškeré stahování dat z IS STAG. Zahrnuje jednotlivé funkce pro volání specifických webových služeb, které po vytvoření vstupních dat volají funkci `save_csv`. Ta pak využívá knihovnu requests pro komunikaci s IS STAG. 

## zakladni_tabulky.py

`zkombinuj_do_vysledku(obor_idno, program_idno, fakulta, program_kod, obor_cislo, rok, semestr)`: Součást procesu obnovy seznamu předmětů, vytvoří ze stažených dat výslednou tabulku pro jeden oborIdno.

`zkombinuj_vysledky(rok)`: Výsledky předchozí funkce sloučí do jedné tabulky. 

`vysledek_pro_katedru(katedra, semestr, rok)`: Načte seznam předmětů, odfiltruje některé sloupce. První krok v generacy výsledného podkladového souboru

## krouzky.py:

`krouzky_a_forma_z_oboru_predmetu(df, katedra, semestr, rok)`: Pomocí informací z WS getOboryPredmetu sloučí předměty s jejich kroužky, sečte jejich počet studentů a přidá formu.

`pridej_minor_krouzky(df_vstup, df_krouzky)`: Ke každému kroužku ve sdruženém studiu přidá jeho protější kroužek.

## rozvrhove_akce.py:

`rozdel_na_rozvrhove_akce(df, katedra, semestr, rok)`: Rozdělí předměty na rozvrhové akce s přiřazenýmy kroužky podle počtu studentů a maximální kapacity typu výuky.

`najdi_aa_akce(df, katedra, semestr, rok)`: Do zadaného dataframu přidá sloupec "Poznámky", ve kterém označí AA akce.

`hledani_spol_vyuky(katedra, semestr, rok)`: Podle rozvrhu z minulého roku katedry získá seznam společné výuky.

## tvorba_finalniho_vysledku.py:

`rozdel_vysledny_soubor(df, katedra, semestr, rok)`: Obsáhlá funkce které doporučí předměty společné výuky a vyučující pomocí dat z předešlého roku. Následně vypočítá zátěž vyučujících a podklasdová data + tuto zátěž zapisuje do výsledného podkladového souboru, čímý tento proces končí.

`sloz_jmeno_ucitele(df)`: Přečte jméno vyučujícího, včetně titulů, z několika sloupců a složí jej do jednoho stringu.

`pricti_zatez(line1, jednotka_hodin, vyucujici_jmeno, vyucujici_paralelVyukaKody, vyucujici_zatez_PS, vyucujici_zatez_KS,vyucujici_zatez_MIX, typ, forma)`: Přičte hodinovou zátěž vyučujícímu. Případně jej přidá do seznamu vyučujících, pokud v něm ještě není.
