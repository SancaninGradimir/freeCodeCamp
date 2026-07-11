import os
import re
import glob

# Translation dictionary: Swahili -> Serbian (for common terms/phrases)
# IMPORTANT: Use word-boundary-safe replacements. Avoid short words that appear inside other words.
translations = {
    # Title patterns
    "Kuchanganya nywila zako": "Heširanje tvojih lozinki",
    "kuchanganya nywila": "heširanje lozinki",
    "changanya nywila": "heširaj lozinku",
    "mchanganyiko": "heš",
    "mchanganyiko.": "heš.",
    "nywila": "lozinka",
    "nywila.": "lozinka.",
    "nywila,": "lozinka,",
    "nywila za": "lozinke za",
    "nywila kama": "lozinku kao",
    "nywila iliyowekwa": "unetu lozinku",
    "nywila zako": "tvoje lozinke",
    "nywila yako": "tvoja lozinka",
    "nenosiri": "lozinka",
    "nenosiri.": "lozinka.",
    
    # Title patterns for hashing file
    "Utekelezaji wa uthibitisho wa utambulisho wa kijamii III": "Implementacija socijalne autentifikacije III",
    "Utekelezaji wa uthibitisho wa utambulisho wa kijamii II": "Implementacija socijalne autentifikacije II",
    "Utekelezaji wa uthibitisho wa utambulisho wa kijamii": "Implementacija socijalne autentifikacije",
    
    # Social auth
    "uthibitisho wa utambulisho": "autentifikacija",
    "uthibitisho": "autentifikacija",
    "kuthibitisha": "autentifikovati",
    "kuthibitishwa": "autentifikovan",
    "ameimethibitishwa": "je autentifikovan",
    "amethibitishwa": "je autentifikovan",
    "imeidhinishwa": "odobrena",
    "alidhinishwa": "odobrio",
    "ameidhinishwa": "odobrio",
    "wakati unapojiandikisha": "kada se registruješ",
    "unapojiandikisha": "kada se registruješ",
    "kujiandikisha": "registracija",
    "kujiandikisha au kuingia": "registracija ili prijava",
    "kujiandikisha au kuingia katika akaunti": "registracija ili prijava na nalog",
    "sajili": "registruj",
    "usajili": "registracija",
    "usajili.": "registracija.",
    "Usajili": "Registracija",
    "kujisajili": "registracija",
    "usajili wa": "registracija",
    
    # Passport
    "mkakati": "strategija",
    "mkakati.": "strategija.",
    "mkakati,": "strategija,",
    "Mkakati": "Strategija",
    "Mikakati": "Strategije",
    "mikakati": "strategije",
    "mikakati mingi": "mnoge strategije",
    "mkakati wa GitHub": "GitHub strategija",
    "Mkakati wa GitHub": "GitHub strategija",
    "mkakati mpya": "nova strategija",
    "mkakati wako": "tvoja strategija",
    "mkakati huo maalum": "te specifične strategije",
    "mkakati wenyewe": "samu strategiju",
    "usanidi wa mkakati": "konfiguracija strategije",
    "usanidi": "konfiguracija",
    "kusanidi": "konfigurisati",
    "kusanidiwa": "konfigurisano",
    
    # Server/App
    "seva": "server",
    "seva.": "server.",
    "seva,": "server,",
    "Seva": "Server",
    "seva yako": "tvoj server",
    "kwenye seva": "na serveru",
    "seva ya mtandao": "web server",
    "seva yako ya": "tvoj server",
    "mtandao": "web",
    "ukurasa": "stranica",
    "ukurasa wako": "tvoja stranica",
    "ukurasa wa nyumbani": "početna stranica",
    "ukurasa wa nyumbani.": "početna stranica.",
    "ukurasa wa nyumbani,": "početna stranica,",
    "Ukurasa": "Stranica",
    "ukurasa wa wasifu": "stranica profila",
    "Ukurasa wako wa nyumbani": "Tvoja početna stranica",
    "ukurasa wako wa nyumbani,": "tvoja početna stranica,",
    "nyumbani": "početna",
    "nyumbani.": "početna.",
    "nyumbani,": "početna,",
    "Nyumbani": "Početna",
    "ukurasa mpya": "nova stranica",
    
    # Authentication
    "Uthibitisho": "Autentifikacija",
    "Uthibitisho ": "Autentifikacija ",
    "Uthibitisho wa": "Autentifikacija",
    "kuthibitishwa": "autentifikovan",
    "kuthibitisha": "autentifikovati",
    "anayethibitishwa": "koji se autentifikuje",
    "yaliyothibitishwa": "autentifikovani",
    "uliyethibitishwa": "autentifikovani",
    "aliyethibitishwa": "autentifikovani",
    "walio imethibitishwa": "su autentifikovani",
    "wakati unapoangalia": "kada proveravaš",
    "kuangalia": "proveravanje",
    "angalia": "proveri",
    "wakati unapoingia": "kada se prijavljuješ",
    "kuingia": "prijava",
    "Kuingia": "Prijava",
    "Ingia": "Prijava",
    "ingia": "prijava",
    "kuingia nje": "odjava",
    "Kuingia nje": "Odjava",
    "Toka": "Odjava",
    "toka": "odjava",
    "kutoka": "odjava",
    "akaanthiwa": "nalog",
    "akaanthiwa.": "nalog.",
    
    # Registration
    "Kujiandikisha": "Registracija",
    "kujiandikisha": "registracija",
    "KWA MTUMIZI": "KORISNIKA",
    "Watumizi wapya": "Novi korisnici",
    "watumizi wapya": "novi korisnici",
    "mtumizi mpya": "novi korisnik",
    "mtumiaji": "korisnik",
    "mtumizi": "korisnik",
    "Mtumizi": "Korisnik",
    "Mtumiaji": "Korisnik",
    "Watumiaji": "Korisnici",
    "watumiaji": "korisnici",
    "watumizi": "korisnici",
    "watumizi waliopo": "trenutnih korisnika",
    "idadi ya watumiaji": "broj korisnika",
    "idadi ya watumiaji waliopo sasa": "broj trenutnih korisnika",
    "idadi ya watumiaji waliopo": "broj trenutnih korisnika",
    "idadi ya watumizi": "broj korisnika",
    "idadi ya watumizi waliopo": "broj trenutnih korisnika",
    "idadi ya watumizi waliopo sasa": "broj trenutnih korisnika",
    "idadi hiyo": "taj broj",
    "hesabu": "brojanje",
    "kigezo cha kuhesabu": "promenljivu za brojanje",
    "kuhesabu": "brojanje",
    "wateja": "klijenti",
    "mteja": "klijent",
    "Mteja": "Klijent",
    "mteja wako": "tvoj klijent",
    
    # Database
    "hifadhidata": "baza podataka",
    "hifadhidata yako": "tvoja baza podataka",
    "hifadhidata ya": "baza podataka",
    "Hifadhidata": "Baza podataka",
    "hifadhi": "sačuvaj",
    "kuhifadhi": "čuvanje",
    "kuhifadhi nywila": "čuvanje lozinki",
    "kuhifadhi akaunti mpya": "čuvanje novog naloga",
    "kwenye hifadhidata": "u bazi podataka",
    "katika hifadhidata": "u bazi podataka",
    "kutoka kwenye hifadhidata": "iz baze podataka",
    "kwenye hifadhidata yako": "u tvojoj bazi podataka",
    
    # Socket/Connection
    "muunganisho": "konekcija",
    "muunganisho mpya": "nova konekcija",
    "Muunganisho": "Konekcija",
    "muunganisho wako": "tvoja konekcija",
    "kutengana": "diskonekcija",
    "kutenganishwa": "diskonektovan",
    "kutengana kwa muunganisho": "diskonekcija",
    "kutengana kunapotokea": "dođe do diskonekcije",
    "kuungana": "povezivanje",
    "kuunganishwa": "povezan",
    "kwa kuunganishwa": "povezivanjem",
    "unaounganishwa": "povezan",
    "wanaounganishwa": "povezani",
    "aliyeungana": "povezan",
    "wanaojiunga": "koji se povezuju",
    "anapo ungana": "se poveže",
    "anapo ungana au kutenganishwa": "se poveže ili diskonektuje",
    "alijiunga": "priključio",
    "alijiunga au akatenganishwa": "priključio ili se odvojio",
    "kujiunga": "pridruživanje",
    "anajiunga": "pridružuje",
    "waliounganishwa": "povezanih",
    "zilizounganishwa": "povezanih",
    "ulizounganisha": "povezao",
    "aliyekuwa anajiunga": "koji se povezuje",
    "ulizounganishwa": "povezani",
    
    # Various
    "njia": "ruta",
    "Njia": "Ruta",
    "njia za data": "rute",
    "njia yako": "tvoja ruta",
    "njia yako ya data": "tvoja ruta",
    "njia ya": "ruta",
    "njia hii": "ova ruta",
    "njia hiyo": "ta ruta",
    "njia ya data": "ruta",
    "kwa njia hii": "na ovoj ruti",
    "Kwa njia hii": "Na ovaj način",
    "kwenye njia": "na ruti",
    "kwa njia": "preko rute",
    "katika njia": "u ruti",
    "kutoka kwenye njia": "sa rute",
    "kwenye njia yako": "na tvojoj ruti",
    
    # Data/Request/Response - use regex for 'data' to avoid partial matches
    "taarifa": "informacije",
    "taarifa zote": "sve informacije",
    "maombi": "zahtevi",
    "ombi": "zahtev",
    "Ombi": "Zahtev",
    "ombi la": "zahtev za",
    "ombi la POST": "POST zahtev",
    "maombi ya GET": "GET zahtevi",
    "jibu": "odgovor",
    "Jibu": "Odgovor",
    "majibu": "odgovori",
    
    # Template/View
    "injini ya templeti": "template engine",
    "injini ya kiolezo": "template engine",
    "kiolezo": "template",
    "kiolezo cha": "template",
    "kiolezo cha Pug": "Pug template",
    "mafaili ya kiolezo": "template fajlovi",
    "faili la kiolezo": "template fajl",
    "faili la templeti": "template fajl",
    "templeti": "template",
    "maoni": "prikazi",
    "mtazamo": "prikaz",
    "Mtazamo": "Prikaz",
    "muonekano": "prikaz",
    "mtazamo wa profaili": "prikaz profila",
    "viungo": "linkovi",
    "kiungo": "link",
    
    # Form
    "fomu": "forma",
    "fomu ya": "forma za",
    "fomu ya usajili": "forma za registraciju",
    "fomu ya kuingia": "forma za prijavu",
    
    # File/Folder
    "faili": "fajl",
    "Faili": "Fajl",
    "faili lako": "tvoj fajl",
    "faili lako la": "tvoj",
    "faili la": "fajl",
    "faili yako": "tvoj fajl",
    "Mafaili": "Fajlovi",
    "mafaili": "fajlove",
    "mafaili mapya": "nove fajlove",
    "mafaili yako": "tvoje fajlove",
    "ndani ya faili": "unutar fajla",
    "kwenye faili": "u fajlu",
    "katika faili": "u fajlu",
    "saraka": "direktorijum",
    
    # Code/Function
    "msimbo": "kod",
    "msimbo wako": "tvoj kod",
    "msimbo uliopo": "postojeći kod",
    "kitendakazi": "funkcija",
    "Kitendakazi": "Funkcija",
    "kitendakazi cha": "funkcija",
    "vitendakazi": "funkcije",
    "hoja": "argument",
    "hoja mbili": "dva argumenta",
    "hoja ya pili": "drugi argument",
    "hoja ya kwanza": "prvi argument",
    "kigezo": "varijabla",
    "kigezo kipya": "nova varijabla",
    "vigezo": "varijable",
    "thamani": "vrednost",
    "thamani za": "vrednosti za",
    "thamani ya": "vrednost",
    "thamani hizo": "te vrednosti",
    
    # Middleware
    "programu ya kati": "middleware",
    "programu ya kati.": "middleware.",
    "Programu ya kati": "Middleware",
    "programu hii ya kati": "ovaj middleware",
    "programu ya kati mpya": "novi middleware",
    
    # Serialization
    "Uwekaji mfululizo": "Serijalizacija",
    "uwekaji mfululizo": "serijalizacija",
    "kuondoa mfululizo": "deserijalizacija",
    "kuweka kitu mfululizo": "serijalizacija objekta",
    "kuweka mfululizo": "serijalizacija",
    "Kuweka mfululizo": "Serijalizacija",
    "mfululizo": "serijalizacija",
    "usimbaji": "serijalizacija",
    "Usimbaji": "Serijalizacija",
    "usimbaji wa kuondoa usimbaji": "deserijalizacija",
    "kuondoa usimbaji": "deserijalizacija",
    "mfululizo na kuondoa mfululizo": "serijalizaciju i deserijalizaciju",
    
    # Cookies/Session
    "kikao": "sesija",
    "vikao": "sesije",
    "kikao cha": "sesija",
    "kikao cha passport": "passport sesija",
    "cookie": "kolačić",
    "cookies": "kolačići",
    
    # Strategy patterns
    "Mkakati wa GitHub unapaswa kuanzishwa vizuri hadi sasa.": "GitHub strategija treba da bude ispravno inicijalizovana do sada.",
    "Usanidi wa mkakati wa GitHub unapaswa kuwa umekamilika.": "Konfiguracija GitHub strategije treba da bude završena.",
    
    # Generic verbs
    "ongeza": "dodaj",
    "Ongeza": "Dodaj",
    "badilisha": "promeni",
    "Badilisha": "Promeni",
    "tengeneza": "napravi",
    "Tengeneza": "Napravi",
    "unda": "napravi",
    "Unda": "Napravi",
    "kuunda": "pravljenje",
    "kuunda mkakati": "pravljenje strategije",
    "kuandaa": "pripremiti",
    "jitayarishe": "pripremi se",
    "kuzuia": "sprečavanje",
    "kukamilisha": "dovršetak",
    "kukamilisha uthibitisho": "dovršetak autentifikacije",
    "kukamilika": "završen",
    "kukamilishwa": "završen",
    "zimekamilika": "završene",
    "imekamilika": "završena",
    "umekamilika": "završen",
    "umefanya vizuri": "si uradio dobro",
    "kumaliza": "završiti",
    "mchakato": "proces",
    "Mchakato": "Proces",
    
    # Remaining specific ones
    "Kurudi kwenye sehemu ya usalama wa habari": "Vraćajući se na deo o bezbednosti informacija",
    "unaweza kukumbuka": "možeš se setiti",
    "kuhifadhi nywila za maandishi wazi": "čuvanje lozinki u otvorenom tekstu",
    "sio sahihi kamwe": "nikada nije ispravno",
    "Sasa ni wakati wa kutekeleza BCrypt kutatua tatizo hili.": "Sada je vreme da implementiraš BCrypt da rešiš ovaj problem.",
    "tayari imeongezwa kama utegemezi": "je već dodata kao zavisnost",
    "hivyo itoe kwenye seva yako": "pa je uvezi na svom serveru",
    "Utahitaji kushughulikia kuchanganya nywila katika maeneo mawili muhimu": "Moraćeš da obradiš heširanje lozinki na dva ključna mesta",
    "pale unapojiandikisha/kuhifadhi akaunti mpya": "kada registruješ/čuvaš novi nalog",
    "na wakati unapoangalia kama nywila ni sahihi wakati wa kuingia": "i kada proveravaš da li je lozinka ispravna prilikom prijave",
    "Kwa sasa kwenye njia yako ya usajili": "Trenutno na tvojoj ruti za registraciju",
    "unaingiza nywila ya mtumizi kama maandishi wazi kwenye hifadhidata kama ifuatavyo": "unosiš korisničku lozinku kao otvoreni tekst u bazu podataka na sledeći način",
    "Badala yake": "Umesto toga",
    "kwa kuongeza yafuatayo kabla ya mantiki ya hifadhidata": "dodavanjem sledećeg pre logike baze podataka",
    "na badilisha": "i zameni",
    "katika kuhifadhi hifadhidata": "u čuvanju baze podataka",
    "Katika mkakati wako wa uthibitisho wa utambulisho": "U tvojoj strategiji autentifikacije",
    "unakagua yafuatayo katika msimbo wako kabla ya kumaliza mchakato": "proveravaš sledeće u svom kodu pre završetka procesa",
    "sasa ni mchanganyiko": "sada je heš",
    "Kabla ya kubadilisha msimbo uliopo": "Pre nego što promeniš postojeći kod",
    "angalia jinsi kauli hiyo inavyokagua kama nywila": "proveri kako ta izjava proverava da li lozinka",
    "si sawa kisha rudisha hali ya kutothibitishwa": "nije ispravna i zatim vraća neautentifikovano stanje",
    "Kwa kuzingatia hili": "Imajući ovo u vidu",
    "badilisha msimbo huo uonekane kama ifuatavyo ili kukagua ipasavyo nywila iliyowekwa dhidi ya mchanganyiko": "promeni taj kod da izgleda ovako kako bi ispravno proverio unetu lozinku protiv heša",
    "Hiyo ndiyo yote inahitajika kutekeleza mojawapo ya vipengele muhimu": "To je sve što je potrebno da se implementira jedna od ključnih bezbednosnih karakteristika",
    "unapo-hifadhi nywila": "kada čuvaš lozinke",
    "Hii inakuwezesha": "Ovo ti omogućava",
    "Inategemea": "Zavisi od",
    "Ni wakati wako": "Vreme je da",
    "kupitia hoja": "kroz argument",
    "kupitisha": "proslediti",
    "kupitishwa": "prosleđen",
    "pitia": "prosledi",
    "Pitia": "Prosledi",
    "pita": "prosledi",
    "pasa": "prosledi",
    "kupita": "proslediti",
    "kupita hoja": "proslediti argument",
    "kwa kupitisha": "prosleđivanjem",
    "kwa kupitisha hoja": "prosleđivanjem argumenta",
    "kupitia hoja yako": "proslediti tvoj argument",
    "kupitia hoja nyingine": "proslediti drugi argument",
    "kama hoja": "kao argument",
    "kwenye hoja": "u argumentu",
    "na hoja": "i argument",
    "kutuma": "slanje",
    "kutuma ombi": "slanje zahteva",
    "kutuma data": "slanje podataka",
    "tuma": "pošalji",
    "Tuma": "Pošalji",
    "kutuma ujumbe": "slanje poruka",
    "ujumbe": "poruka",
    "ujumbe wa": "poruke",
    "Ujumbe": "Poruka",
    
    # Hints/Assertions
    "inapaswa": "treba",
    "inapaswa kuwa": "treba da bude",
    "inapaswa kuitwa": "treba da se pozove",
    "inapaswa kufafanuliwa": "treba da bude definisana",
    "inapaswa kusanidiwa": "treba da bude konfigurisana",
    "inapaswa kuhitajika": "treba da bude zahtevana",
    "inapaswa kuwa na": "treba da ima",
    "inapaswa kuwa umekamilika": "treba da bude završen",
    "inapaswa kuwa sahihi": "treba da bude ispravna",
    "inapaswa kuwa sawa": "treba da bude ispravna",
    "inapaswa kutekelezwa": "treba da bude implementirana",
    "inapaswa kusiwa": "treba da sluša",
    "inapaswa kutumika": "treba da se koristi",
    "inapaswa kusikiliza": "treba da sluša",
    "inapaswa kuitwa na": "treba da se pozove sa",
    "inapaswa kusanidiwa": "treba da bude konfigurisana",
    "unapaswa": "treba",
    "Unapaswa": "Treba",
    "Unapaswa kuwa na": "Treba da imaš",
    "unapaswa kuwa na": "treba da imaš",
    "unapaswa kuwa ume": "treba da si",
    "unapaswa kuongeza": "treba da dodaš",
    "unapaswa kuomba": "treba da uvezeš",
    "unapaswa kusanidi": "treba da konfigurišeš",
    "unapaswa kutumia": "treba da koristiš",
    "unapaswa kufanya": "treba da uradiš",
    "unapaswa kusikiliza": "treba da slušaš",
    "unapaswa kushughulikia": "treba da obradiš",
    "unapaswa kuweka": "treba da postaviš",
    "unapaswa kuhakikisha": "treba da osiguraš",
    "unapaswa kuhitaji": "treba da zahtevaš",
    "unapaswa kuongeza": "treba da dodaš",
    "unapaswa kuunda": "treba da napraviš",
    "unapaswa kuwa": "treba da budeš",
    "unapaswa kuwa umeondoa": "treba da si uklonio",
    "unapaswa kuwa na njia": "treba da imaš rutu",
    "unapaswa kuwa na kitendakazi": "treba da imaš funkciju",
    "unapaswa kuwa na msimbo": "treba da imaš kod",
    
    # Various remaining
    "Neno kuu": "Ključna reč",
    "neno kuu": "ključna reč",
    "mfuatano": "string",
    "Mfuatano": "String",
    "mfuatano wa": "string",
    "hatua": "korak",
    "Hatua": "Korak",
    "hatua hii": "ovaj korak",
    "Changamoto": "Izazov",
    "changamoto": "izazov",
    "changamoto hizi": "ovi izazovi",
    "changamoto hii": "ovaj izazov",
    "chaguzi": "opcije",
    "chaguo-msingi": "podrazumevano",
    
    # Environment
    "mazingira": "okruženje",
    "kigezo cha mazingira": "promenljiva okruženja",
    "vigezo vyako vya mazingira": "tvoje promenljive okruženja",
    
    # More specific
    "Kitu cha kwanza kinachohitaji kushughulikiwa": "Prva stvar koju treba obraditi",
    "kitu": "objekat",
    "kitu kipya": "novi objekat",
    "kitu cha mtumiaji": "korisnički objekat",
    "kitu cha mtumizi": "korisnički objekat",
    "kitu kamili cha mtumizi": "celi korisnički objekat",
    "kitu cha data": "data objekat",
    "sifa": "osobina",
    
    # Wrapping up
    "Jaribu": "Probaj",
    "jaribu": "probaj",
    "Sasa": "Sada",
    "sasa": "sada",
    "Hapa": "Ovde",
    "hapa": "ovde",
    "hapo": "tamo",
    "hapo juu": "gore",
    "Hiyo": "To",
    "hiyo": "to",
    "hii": "ovo",
    "Hii": "Ovo",
    "hili": "ovo",
    "kwa hili": "za ovo",
    "kutoka kwa watoa huduma": "od provajdera",
    
    # Simple word swaps
    "pamoja na": "zajedno sa",
    "kwa mfano": "na primer",
    "Kwa mfano": "Na primer",
    "kwa hivyo": "tako da",
    "Kwa hivyo": "Tako da",
    "kwa sababu": "jer",
    "Kwa sababu": "Jer",
    "na": "i",
    "Na ": "I ",
    "lakini": "ali",
    "au": "ili",
    "bila": "bez",
    "kama": "kao",
    "Kama": "Kao",
    "kama ilivyo": "kao što je",
    "kama ifuatavyo": "na sledeći način",
    "kama ifuatavyo:": "na sledeći način:",
    "kama inavyoonyeshwa": "kao što je prikazano",
    "kama inavyoonyeshwa hapa chini": "kao što je prikazano ispod",
    "kama vile": "kao što su",
    "hivyo": "tako",
    "Hivyo": "Tako",
    "bado": "još",
    "pia": "takođe",
    "Pia": "Takođe",
    "zaidi": "više",
    "sana": "veoma",
    "sawa": "slično",
    "mwishowe": "konačno",
    "Mwishowe": "Konačno",
    "kweli": "stvarno",
    "Kama ilivyo sasa": "Kao što je sada",
    "kama ilivyo sasa": "kao što je sada",
    "ila": "osim",
    "isipokuwa": "osim",
    
    # Chat
    "gumzo": "ćaskanje",
    "gumzo.": "ćaskanje.",
    "gumzo:": "ćaskanje:",
    "mazungumzo": "ćaskanje",
    "Mazungumzo": "Ćaskanje",
    "mazungumzo.": "ćaskanje.",
    "ujumbe wa gumzo": "poruke ćaskanja",
    
    # from server.js / auth.js context
    "Wasilisha ukurasa wako unapoona umefanya vizuri.": "Predaj svoju stranicu kada vidiš da si uradio dobro.",
    "Ikiwa unakutana na makosa": "Ako naiđeš na greške",
    "unaweza": "možeš",
    "kuangalia mradi uliofanyika": "pogledati projekat koji je urađen",
    "kuangalia mradi uliofanyika hadi sasa": "pogledati projekat urađen do sada",
    "kuangalia mradi uliofanyika hadi hatua hii": "pogledati projekat urađen do ovog koraka",
    "kuangalia mradi uliofanyika hadi hatua hii.": "pogledati projekat urađen do ovog koraka.",
    "kuangalia mfano wa mradi ulio kamilika": "pogledati primer završenog projekta",
    "kagua mradi uliofanyika": "pogledaj projekat urađen",
    "kagua mradi uliofanyika hadi sasa": "pogledaj projekat urađen do sada",
    "kagua mradi uliofanyika hadi hatua hii": "pogledaj projekat urađen do ovog koraka",
    "kagua mradi uliofikia hatua hii": "pogledaj projekat koji je stigao do ovog koraka",
    "kagua mradi hadi hatua hii": "pogledaj projekat do ovog koraka",
    "makosa": "greške",
    "Makosa": "Greške",
    "kosa": "greška",
    "hitilafu": "greška",
    "Hitilafu": "Greška",
    "Kosa": "Greška",
    
    # Specific to the content
    "Hivyo katika": "Tako u",
    "hivyo katika": "tako u",
    "ndani yake": "unutar njega",
    "ndani ya": "unutar",
    "ndani mwa": "unutar",
    
    # Yes/No/Callback
    "wito wa kurudisha": "callback",
    "wito wa mwitiko": "callback",
    "kitendakazi cha mwitiko": "callback funkcija",
    "kitendakazi kinachoitwa": "funkcija koja se poziva",
    "kurudisha": "vraćanje",
    "rudisha": "vrati",
    "Rudisha": "Vrati",
    "Wito": "Poziv",
    "wito": "poziv",
    "kwamba": "da",
    "kama": "da li",
    
    # More terms from files
    "kutolewa": "emitovan",
    "toa": "emituj",
    "Kwa sasa": "Trenutno",
    "kwa sasa": "trenutno",
    "kwenye programu yako": "u tvojoj aplikaciji",
    "kutoka kwenye programu yako": "iz tvoje aplikacije",
    "mtumizi anayeupata upatikanaji": "korisnik koji dobija pristup",
    "upatikanaji": "pristup",
    "kwa upatikanaji": "za pristup",
    "kupata upatikanaji": "dobiti pristup",
    "Utekelezaji": "Implementacija",
    "utekelezaji": "implementacija",
    "kutekeleza": "implementirati",
    "tekeleza": "implementiraj",
    "Tekeleza": "Implementiraj",
    "kutekelezwa": "implementirana",
    "imeanzishwa": "instalirana",
    "imewekwa": "podešena",
    "imeongezwa": "dodata",
    "zimeongezwa": "dodate",
    "umesakinishwa": "instaliran",
    "zimesakinishwa": "instalirane",
    "imepakuliwa": "preuzeta",
    "Imeletwa": "Uvezeno",
    
    # Security
    "usalama": "bezbednost",
    "usalama wa habari": "bezbednost informacija",
    "usalama unapo-hifadhi": "bezbednost kada čuvaš",
    "kwa usalama": "bezbednosno",
    
    # Passport/Local
    "ya ndani": "lokalna",
    "kwa njia ya ndani": "lokalno",
    "kwa kutumia jina la mtumizi na nenosiri": "koristeći korisničko ime i lozinku",
    "jina la mtumizi": "korisničko ime",
    "jina la mtumiaji": "korisničko ime",
    "Jina la mtumizi": "Korisničko ime",
    
    # Serialization specific
    "ikiwa ni pamoja na": "uključujući",
    "ikiwa ni pamoja na ObjectId": "uključujući ObjectId",
    "huenda": "možda",
    "Huenda": "Možda",
    
    # MongoDB
    "muunganisho wa": "konekcija sa",
    "muunganisho wa hifadhidata": "konekcija sa bazom podataka",
    "muunganisho wa kudumu": "trajna konekcija",
    "mzunguko mzima wa maisha": "ceo životni ciklus",
    "maisha ya programu": "životni ciklus aplikacije",
    "programa": "aplikacija",
    
    # GitHub OAuth
    "Kitambulisho cha mteja": "ID klijenta",
    "kitambulisho cha mteja": "ID klijenta",
    "Kitambulisho": "ID",
    "siri ya mteja": "tajna klijenta",
    "siri zilizopatikana": "dobijene tajne",
    "tokeni ya upatikanaji": "access token",
    "tokeni ya onyesha upya": "refresh token",
    "tokeni za OAuth 2.0": "OAuth 2.0 tokeni",
    
    # Profile
    "wasifu": "profil",
    "wasifu wako": "tvoj profil",
    "wasifu wake": "njegov profil",
    "wasifu unaorudishwa": "profil koji se vraća",
    "wasifu unaorudiwa": "profil koji se vraća",
    "wasifu huo": "taj profil",
    "wasifu wa GitHub": "GitHub profil",
    "wasifu aliyethibitishwa": "autentifikovani profil",
    "profaili": "profil",
    "Profaili": "Profil",
    
    # Db operations
    "utafutaji": "pretraga",
    "tafuta": "pretraži",
    "Tafuta": "Pretraži",
    "kutafuta": "traženje",
    "kutafuta kitu": "traženje objekta",
    "inaweza kuitumia kutafuta": "možeš ga koristiti za pretragu",
    "kuitumia kutafuta": "koristiti za pretragu",
    
    # Various verbs
    "fungua": "otvori",
    "Fungua": "Otvori",
    "kufungua": "otvaranje",
    "kufungua wateja zaidi": "otvaranje više klijenata",
    "kufuta": "brisanje",
    "futa": "obriši",
    
    # More small connectors
    "kisha": "zatim",
    "Kisha": "Zatim",
    "basi": "onda",
    "Basi": "Onda",
    "hata": "čak",
    "kuhusu": "o",
    
    # Time
    "wakati": "vreme",
    "Wakati": "Vreme",
    "Wakati una": "Kada",
    "wakati una": "kada",
    "wakati huo": "tada",
    
    # Template specific
    "imeshindwa": "neuspešno",
    "mafanikio": "uspeh",
    "umefanikiwa": "uspešno",
    "kwa mafanikio": "uspešno",
    "na kama ni halali": "i da li je validan",
    "halali": "validan",
    "kwa usahihi": "ispravno",
    "ipasavyo": "ispravno",
    "sahihi": "ispravno",
    
    # Project
    "mradi": "projekat",
    "mradi huu": "ovaj projekat",
    "Mradi": "Projekat",
    "mradi wako": "tvoj projekat",
    
    # More
    "msaidizi": "pomoćnik",
    "msaada": "pomoć",
    "muhimu": "važno",
    "Muhimu": "Važno",
    
    # Routes
    "elekeza upya": "preusmeri",
    "Elekeza upya": "Preusmeri",
    "kuelekeza upya": "preusmeravanje",
    "uelekeze upya": "preusmeri",
    "kuelekezwa upya": "preusmeren",
    "kuelekeza upya kwenda": "preusmeravanje na",
    "kuelekeza upya kwenye": "preusmeravanje na",
    
    # Strategy config
    "inayokubali hoja 2": "koji prihvata 2 argumenta",
    "inayopokea": "koji prima",
    "unapokea": "primaš",
    "hupokea": "prima",
    "kupokea": "primanje",
    
    # query
    "hoja ya utafutaji": "upit za pretragu",
    "Fanya hoja ya utafutaji": "Napravi upit za pretragu",
    "fanya hoja ya utafutaji": "napravi upit za pretragu",
    
    # ObjectID
    "inayozalishwa": "koji se generiše",
    "zina": "imaju",
    "kwa kutumia": "koristeći",
    
    # Testing
    "tahadhari": "upozorenje",
    "onyo": "upozorenje",
    "Onyo": "Upozorenje",
    "maelekezo": "uputstva",
    
    # More small ones
    "Hiki": "Ovo",
    "hiki": "ovo",
    "Somo": "Lekcija",
    "somo": "lekcija",
    
    # Chat terms
    "orodha isiyopangwa": "neuređena lista",
    "orodha": "lista",
    
    # Lines/code 
    "mistari": "linije",
    "mstari": "linija",
    "mfano": "primer",
    "Mfano": "Primer",
    
    # Remaining terms from the files
    "sehemu": "deo",
    "Sehemu": "Deo",
    "sehemu za": "delovi",
    "Sehemu ya mwisho": "Poslednji deo",
    "Sehemu ya mwisho ya mkakati": "Poslednji deo strategije",
    "kushughulikia": "obrada",
    "kushughulikia wasifu": "obrada profila",
    "kushughulikia hili": "obrada ovoga",
    "shughulikia": "obradi",
    "Shughulikia": "Obradi",
    "kushughulikiwa": "obrađen",
    "kushughulikiwa ndani ya": "obrađen unutar",
    "hushughulikiwa": "obrađuje se",
    "hushughulikiwa ndani ya": "obrađuje se unutar",
    
    "kupakia": "učitavanje",
    "pakua": "učitaj",
    "Pakua": "Učitaj",
    "kitu cha mtumiaji": "korisnički objekat",
    "kitu cha mtumizi katika hifadhidata": "korisnički objekat u bazi podataka",
    "ikiwa kipo": "ako postoji",
    "au kuunda kipya ikiwa hakipo": "ili kreirati novi ako ne postoji",
    "kujaza sehemu": "popunjavanje polja",
    "kutoka kwenye wasifu": "iz profila",
    
    "inatupa": "daje nam",
    "hutupatia": "daje nam",
    "ili kusanifu": "da standardizujemo",
    "ambayo tayari imetekelezwa": "koja je već implementirana",
    "Hapa chini ni mfano wa utekelezaji": "Ispod je primer implementacije",
    "unaweza kutumia": "možeš koristiti",
    "unaenda ndani ya kitendakazi": "ide unutar funkcije",
    "hoja ya pili kwa mkakati mpya": "drugi argument za novu strategiju",
    "chini kabisa ya mahali": "odmah ispod mesta",
    "iko sasa": "se nalazi",
    
    "inakuwezesha kutafuta kitu na kukiboresha": "omogućava ti da pretražiš objekat i ažuriraš ga",
    "kitaingizwa": "biće umetnut",
    "kutolewa kwa kitendakazi cha mwitiko": "prosleđen callback funkciji",
    "kila mara tunaweka": "uvek postavljamo",
    "kuongezea": "povećavamo",
    "na kujaza sehemu nyingi tu wakati kitu kipya kinaingizwa": "i popunjavamo ostala polja samo kada se novi objekat ubacuje",
    "Angalia matumizi ya thamani za msingi": "Obrati pažnju na upotrebu podrazumevanih vrednosti",
    "Wakati mwingine wasifu unaorudishwa hautakuwa na taarifa zote zimejazwa": "Ponekad profil koji se vraća neće imati sve informacije popunjene",
    "au mtumiaji ataweka kuwa faragha": "ili će korisnik postaviti kao privatno",
    "Katika hali hii, unashughulikia ili kuzuia kosa": "U ovom slučaju, obrađuješ da sprečiš grešku",
    "Sasa unapaswa kuweza kuingia kwenye programu yako": "Sada bi trebalo da možeš da se prijaviš na svoju aplikaciju",
    "Jaribu!": "Probaj!",
    
    # More terms from social auth
    "Njia msingi ambayo uthibitisho huu wa aina hii utakayo fuata": "Osnovni način na koji će ova vrsta autentifikacije pratiti",
    "Mtumizi anabofya kitufe au kiungo": "Korisnik klikne dugme ili link",
    "kinachompeleka kwenye njia yako ya data": "koji ga vodi na tvoju rutu",
    "kuthibitisha utambulisho kwa kutumia mkakati maalum": "autentifikaciju koristeći specifičnu strategiju",
    "inaita": "poziva",
    "ambayo inaelekeza upya mtumizi kwenda GitHub": "koja preusmerava korisnika na GitHub",
    "Ukurasa ambao mtumizi anafika": "Stranica na koju korisnik stiže",
    "unamruhusu kuingia ikiwa bado hajajiunga": "mu dozvoljava da se prijavi ako već nije",
    "Kisha unamuomba kuruhusu upatikanaji wa wasifu wake": "Zatim ga pita da dozvoli pristup svom profilu",
    "kutoka kwenye programu yako": "iz tvoje aplikacije",
    "Mtumizi kisha anarudishwa kwenye programu yako": "Korisnik se zatim vraća u tvoju aplikaciju",
    "kwenye URL maalum ya wito wa kurudisha": "na specifični callback URL",
    "na wasifu wake ikiwa ameidhinishwa": "sa svojim profilom ako je odobrio",
    "Sasa yuko imethibitishwa": "Sada je autentifikovan",
    "na programu yako inapaswa kukagua": "i tvoja aplikacija treba da proveri",
    "kama ni wasifu unaorudiwa": "da li je profil koji se vraća",
    "au kuihifadhi kwenye hifadhidata yako ikiwa siyo": "ili da ga sačuva u tvojoj bazi podataka ako nije",
    
    "Mikakati yenye OAuth inahitaji uwe na angalau": "OAuth strategije zahtevaju da imaš najmanje",
    "ambayo ni njia ya huduma kuthibitisha ni nani anayetuma ombi la uthibitisho": "koji je način da servis potvrdi ko šalje zahtev za autentifikaciju",
    "na kama ni halali": "i da li je validan",
    "Hizi hupatikana kutoka kwenye tovuti": "Ovo se dobija sa sajta",
    "unajaribu kutekeleza uthibitisho nayo": "pokušavaš da implementiraš autentifikaciju sa",
    "na ni za kipekee kwa programu yako": "i jedinstveni su za tvoju aplikaciju",
    "HAZITAKIWA KUSHIRIKIWA": "NE SMEJU SE DELITI",
    "hazipaswi kamwe kupakiwa kwenye hifadhidata ya umma": "nikada ne smeju biti postavljeni u javni repozitorijum",
    "au kuandikwa moja kwa moja kwenye msimbo wako": "ili direktno napisani u tvom kodu",
    "Mazoezi ya kawaida": "Uobičajena praksa",
    "ni kuzihifadhi kwenye faili lako la .env": "je da ih čuvaš u tvom .env fajlu",
    "na kuzirejea kama": "i referenciraš ih kao",
    "Kwa changamoto hii utatumia mkakati wa GitHub": "Za ovaj izazov koristićeš GitHub strategiju",
    "Fuata maelekezo haya": "Prati ova uputstva",
    "Weka URL ya ukurasa wa nyumbani kuwa ukurasa wako wa nyumbani": "Postavi URL početne stranice na svoju početnu stranicu",
    "si URL ya msimbo wa mradi": "ne URL koda projekta",
    "na weka URL ya wito wa kurudisha kuwa URL ile ile": "i postavi callback URL na isti URL",
    "na imeambatanishwa mwishoni": "sa dodatkom na kraju",
    "Hifadhi client ID na siri ya mteja kwenye faili": "Sačuvaj client ID i client secret u fajlu",
    
    "Katika faili lako la routes.js": "U tvom routes.js fajlu",
    "ongeza showSocialAuth: true": "dodaj showSocialAuth: true",
    "kwenye njia ya ukurasa wa nyumbani, baada ya showRegistration: true": "na rutu početne stranice, posle showRegistration: true",
    "Sasa, tengeneza njia mbili za data": "Sada, napravi dve rute",
    "zinazokubali maombi ya GET": "koje prihvataju GET zahteve",
    "Ya kwanza inapaswa kuitwa passport tu kuthibitisha": "Prva treba samo da pozove passport da autentifikuje",
    "Ya pili inapaswa kuitwa passport kuthibitisha": "Druga treba da pozove passport da autentifikuje",
    "na ikiwa itashindwa elekeza upya kwenda /": "i ako ne uspe preusmeri na /",
    "kisha ikiwa itafanikiwa elekeza upya kwenda /profile": "zatim ako uspe preusmeri na /profile",
    "kama ilivyo kwenye mradi wako wa mwisho": "kao što je u tvom poslednjem projektu",
    "Mfano wa jinsi inavyopaswa kuonekana": "Primer kako treba da izgleda",
    "kama jinsi ulivyoshughulikia kuingia kawaida": "kao što si obradio običnu prijavu",
    
    # Social auth II
    "Sehemu ya mwisho ya kuanzisha uthibitisho wako wa GitHub": "Poslednji deo postavljanja tvoje GitHub autentifikacije",
    "ni kuunda mkakati wenyewe": "je kreiranje same strategije",
    "tayari imeongezwa kama utegemezi": "je već dodata kao zavisnost",
    "kwa hivyo itaombea katika faili lako la auth.js": "pa je uvezi u svom auth.js fajlu",
    "kama GitHubStrategy hivi": "kao GitHubStrategy ovako",
    "Usisahau kuomba na kusanidi dotenv": "Ne zaboravi da uvezeš i konfigurišeš dotenv",
    "ili itumie vigezo vyako vya mazingira": "da koristi tvoje promenljive okruženja",
    "Ili kuanzisha mkakati wa GitHub": "Da bi postavio GitHub strategiju",
    "lazima uambie Passport itumie GitHubStrategy iliyotengenezwa": "moraš reći Passportu da koristi kreiranu GitHubStrategy",
    "ambayo inakubali hoja 2": "koja prihvata 2 argumenta",
    "kitu (chenye clientID, clientSecret, na callbackURL)": "objekat (sa clientID, clientSecret, i callbackURL)",
    "na kitendakazi kinachoitwa wakati mtumizi amethibitishwa kwa mafanikio": "i funkciju koja se poziva kada je korisnik uspešno autentifikovan",
    "ambacho kitabaini kama mtumizi ni mpya": "koja će utvrditi da li je korisnik nov",
    "na ni sehemu gani za kuhifadhi awali katika kitu cha mtumizi katika hifadhidata": "i koje delove sačuvati u korisničkom objektu u bazi podataka",
    "Hii ni kawaida kwa mikakati mingi": "Ovo je uobičajeno za većinu strategija",
    "lakini baadhi zinaweza kuhitaji taarifa zaidi": "ali neke mogu zahtevati više informacija",
    "kama ilivyoelezwa katika README ya mkakati huo maalum": "kao što je opisano u README te specifične strategije",
    "Kwa mfano, Google pia inahitaji wigo": "Na primer, Google takođe zahteva opseg",
    "unaooamua aina gani ya taarifa ombi lako linataka kurudishwa": "koji određuje koju vrstu informacija tvoj zahtev želi da vrati",
    "na huomba mtumizi kuidhinisha upatikanaji huo": "i traži od korisnika da odobri taj pristup",
    "Mkakati unaotekeleza sasa": "Strategija koju sada implementiraš",
    "unathibitisha watumizi kwa kutumia akaunti ya GitHub": "autentifikuje korisnike koristeći GitHub nalog",
    "na tokeni za OAuth 2.0": "i OAuth 2.0 tokenima",
    "Kitambulisho cha mteja na siri zilizopatikana": "ID klijenta i tajna dobijeni",
    "wakati wa kuunda programu": "prilikom kreiranja aplikacije",
    "hutolewa kama chaguo wakati wa kuunda mkakati": "se daju kao opcije prilikom kreiranja strategije",
    "Mkakati pia unahitaji wito wa kurudisha verify": "Strategija takođe zahteva verify callback",
    "unaopokea tokeni ya upatikanaji na tokeni ya onyesha upya hiari": "koji prima access token i opcioni refresh token",
    "pamoja na profile inayojumuisha wasifu": "zajedno sa profilom koji uključuje profil",
    "wa mtumizi aliyethibitishwa wa GitHub": "autentifikovanog GitHub korisnika",
    "Wito wa kurudisha verify lazima uitwe cb": "Verify callback mora biti pozvan cb",
    "ukitoa mtumizi ili kukamilisha uthibitisho": "dajući korisnika da dovrši autentifikaciju",
}

# Function to translate Swahili text in a file to Serbian
def translate_text(text):
    # Sort keys by length (longest first) to avoid partial replacements
    sorted_keys = sorted(translations.keys(), key=len, reverse=True)
    
    # Replace Swahili with Serbian
    for swahili in sorted_keys:
        serbian = translations[swahili]
        text = text.replace(swahili, serbian)
    
    # Handle 'data' word specifically with word boundaries to avoid partial matches
    # Replace 'data' only when it appears as a standalone word (not inside other words)
    text = re.sub(r'\bdata\b', 'podaci', text)
    text = re.sub(r'\bData\b', 'Podaci', text)
    
    return text

# Define all .md files in the folder
folder = "curriculum/i18n-curriculum/curriculum/challenges/swahili/blocks/advanced-node-and-express"
files = sorted(glob.glob(os.path.join(folder, "*.md")))

# Filter out .bak files
md_files = [f for f in files if not f.endswith('.bak')]

print(f"Found {len(md_files)} .md files to process.")

for filepath in md_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract frontmatter and body
    parts = content.split('---')
    
    if len(parts) >= 3:
        # Reconstruct with translation of the text parts
        # The frontmatter is parts[1]
        frontmatter = parts[1]
        
        # Translate title in frontmatter
        new_frontmatter = translate_text(frontmatter)
        
        # The body is everything after the second ---
        body = '---'.join(parts[2:])
        
        # Only translate text outside code blocks
        new_body_parts = []
        code_block = False
        current_lines = []
        
        for line in body.split('\n'):
            if line.strip().startswith('```'):
                if code_block:
                    # End of code block
                    new_body_parts.extend(current_lines)
                    new_body_parts.append(line)
                    current_lines = []
                    code_block = False
                else:
                    # Start of code block
                    if current_lines:
                        translated = translate_text('\n'.join(current_lines))
                        new_body_parts.append(translated)
                        current_lines = []
                    new_body_parts.append(line)
                    code_block = True
            else:
                if code_block:
                    new_body_parts.append(line)
                else:
                    current_lines.append(line)
        
        if current_lines:
            translated = translate_text('\n'.join(current_lines))
            new_body_parts.append(translated)
        
        new_body = '\n'.join(new_body_parts)
        
        # Reconstruct the full file
        new_content = '---' + new_frontmatter + '---' + new_body
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Translated: {os.path.basename(filepath)}")
    else:
        print(f"WARNING: Could not parse frontmatter in {filepath}")

print("\nAll files translated!")