import json
import sys

# Read the original file
with open('client/i18n/locales/swahili/intro.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

keys = list(data.keys())

# Translation map for sections 1-20 (indices 0-19)
# Format: (key_path, value) or we build the translation dict

# Let's create a function that translates each section
def translate_text(text):
    """Translate common Swahili/English curriculum text to Serbian."""
    if not isinstance(text, str):
        return text
    
    # Curriculum superblock/block titles and descriptions
    translations = {
        # Superblock titles
        "Changamoto za Ubunifu wa Wavuti Sikivu": "Legacy Responsive Web Design Izazovi",
        "Legacy Responsive Web Design V8": "Legacy Responsive Web Design V8",
        "Legacy JavaScript Algorithms and Data Structures V7": "Legacy JavaScript Algoritmi i Strukture Podataka V7",
        "Legacy JavaScript Algorithms and Data Structures V8": "Legacy JavaScript Algoritmi i Strukture Podataka V8",
        "Front-End Development Libraries V8": "Front-End Development Biblioteke V8",
        "Data Visualization V8": "Vizuelizacija Podataka V8",
        "Learn Data Visualization with D3": "Nauči Vizuelizaciju Podataka sa D3",
        "Relational Database V8": "Relaciona Baza Podataka V8",
        "Back-End Development and APIs V8": "Back-End Development i API-ji V8",
        "Ubora (Quality Assurance)": "Quality Assurance",
        "Scientific Computing with Python": "Naučno Računanje sa Python-om",
        "Data Analysis na Python": "Analiza Podataka sa Python-om",
        "Learn Python for Beginners": "Nauči Python za Početnike",
        "Introduction to Algorithms and Data Structures": "Uvod u Algoritme i Strukture Podataka",
        "Learn RAG and MCP Fundamentals": "Nauči RAG i MCP Osnove",
        "Introduction to Precalculus": "Uvod u Prekalkulus",
        "Introduction to Bash": "Uvod u Bash",
        "Introduction to SQL and PostgreSQL": "Uvod u SQL i PostgreSQL",
        "Learn Bash Scripting": "Nauči Bash Skriptovanje",
        "Learn SQL and Bash": "Nauči SQL i Bash",

        # Block titles that are in English
        "Learn More About CSS Pseudo Selectors by Building A Balance Sheet": "Nauči Više o CSS Pseudo Selektore Gradeći Bilansni Izveštaj",
        "Learn Intermediate CSS by Building a Cat Painting": "Nauči Intermediate CSS Gradeći Sliku Mačke",
        
        # Section 4 - English intro text
        "Developers use HTML and CSS to control the content and styling of a page. And they use JavaScript to make that page interactive.": "Developeri koriste HTML i CSS za kontrolu sadržaja i stilizaciju stranice. A koriste JavaScript da bi stranicu učinili interaktivnom.",
        "In this JavaScript Algorithm and Data Structures Certification, you'll learn the JavaScript fundamentals like variables, arrays, objects, loops, functions, the DOM and more.": "U ovom JavaScript Algoritmi i Strukture Podataka Sertifikatu, naučićeš JavaScript osnove kao što su varijable, nizovi, objekti, petlje, funkcije, DOM i više.",
        "You'll also learn about Object Oriented Programming (OOP), Functional Programming, algorithmic thinking, how to work with trees, and more.": "Takođe ćeš naučiti o Objektno-Orijentisanom Programiranju (OOP), Funkcionalnom Programiranju, algoritamskom razmišljanju, kako raditi sa stablima, i više.",
        
        # Section 5
        "Now that you're familiar with HTML, CSS, and JavaScript, level up your skills by learning some of the most popular front-end libraries in the industry.": "Sada kada si upoznat sa HTML, CSS i JavaScript-om, unapredi svoje veštine učeći neke od najpopularnijih front-end biblioteka u industriji.",
        "In the Front-End Development Libraries Certification, you'll learn how to style your site quickly with Bootstrap. You'll also learn how to add logic to your CSS styles and extend them with Sass.": "U Front-End Development Biblioteke Sertifikatu, naučićeš kako da brzo stilizuješ svoj sajt sa Bootstrap-om. Takođe ćeš naučiti kako da dodaš logiku svojim CSS stilovima i proširiš ih sa Sass-om.",
        
        # Section 11
        "The Scientific Computing with Python curriculum will equip you with the skills to analyze and manipulate data using Python.": "Naučno Računanje sa Python-om kurikulum će te opremiti veštinama za analizu i manipulaciju podacima koristeći Python.",
        "This comprehensive course will guide you through the fundamentals of scientific computing, including data structures, and algorithms.": "Ovaj sveobuhvatni kurs će te provesti kroz osnove naučnog računanja, uključujući strukture podataka i algoritme.",
        
        # Section 13
        "Python is one of the most popular programming languages today. It's easy to learn, readable, and versatile.": "Python je jedan od najpopularnijih programskih jezika danas. Lako se uči, čitljiv je i svestran.",
        "In this comprehensive course, you'll learn the fundamentals of Python programming from the ground up. You'll start with setting up Python and writing your first program.": "U ovom sveobuhvatnom kursu, naučićeš osnove Python programiranja od samog početka. Počećeš sa podešavanjem Pythona i pisanjem svog prvog programa.",
        
        # Section 14
        "Algorithms and Data Structures are the backbone of programming. So it's important to learn how to work with them.": "Algoritmi i Strukture Podataka su kičma programiranja. Zato je važno naučiti kako raditi sa njima.",
        "In this comprehensive course, you will learn about common sorting and searching algorithms including merge sort, quicksort, binary search, and more.": "U ovom sveobuhvatnom kursu, naučićeš o uobičajenim algoritmima sortiranja i pretrage uključujući merge sort, quicksort, binarnu pretragu i više.",
        "You will also learn how to work with common data structures including arrays and linked lists.": "Takođe ćeš naučiti kako raditi sa uobičajenim strukturama podataka uključujući nizove i povezane liste.",
        
        # Section 15
        "RAG stands for Retrieval-Augmented Generation. MCP stands for Model Context Protocol. These are powerful frameworks for building AI applications.": "RAG označava Retrieval-Augmented Generation. MCP označava Model Context Protocol. Ovo su moćni okviri za izgradnju AI aplikacija.",
        "In this course, you'll learn the fundamentals of RAG and MCP and how to implement them in your own projects. You'll explore various tools and techniques.": "U ovom kursu, naučićeš osnove RAG i MCP i kako ih implementirati u svojim projektima. Istražićeš različite alate i tehnike.",
        
        # Section 16
        "Precalculus is a branch of mathematics that prepares you for calculus. It covers a wide range of topics including functions, trigonometry, and more.": "Prekalkulus je grana matematike koja te priprema za kalkulus. Pokriva širok spektar tema uključujući funkcije, trigonometriju i više.",
        
        # Section 17
        "Bash is a Unix shell and command language that provides a powerful interface for interacting with your computer's operating system.": "Bash je Unix školjka i komandni jezik koji pruža moćan interfejs za interakciju sa operativnim sistemom računara.",
        "In this course, you'll learn the basics of Bash scripting, including how to navigate the file system, manipulate files and more.": "U ovom kursu, naučićeš osnove Bash skriptovanja, uključujući kako navigirati kroz sistem datoteka, manipulisati datotekama i više.",
        
        # Section 18
        "SQL (Structured Query Language) is a programming language used to manage and manipulate relational databases. It allows you to create, read, update, and delete data.": "SQL (Structured Query Language) je programski jezik koji se koristi za upravljanje i manipulaciju relacionim bazama podataka. Omogućava ti da kreiraš, čitaš, ažuriraš i brišeš podatke.",
        "PostgreSQL is a powerful, open-source relational database management system that uses SQL as its query language. It provides advanced features and reliability.": "PostgreSQL je moćan, open-source sistem za upravljanje relacionim bazama podataka koji koristi SQL kao svoj jezik za upite. Pruža napredne funkcije i pouzdanost.",
        
        # Section 19
        "Bash scripts combine terminal commands and logic into programs that can execute or automate tasks, and much more.": "Bash skriptovi kombinuju terminal komande i logiku u programe koji mogu izvršavati ili automatizovati zadatke, i mnogo više.",
        "In this course, you will learn more terminal commands and how to use them within Bash scripts by creating five small programs.": "U ovom kursu, naučićeš više terminal komandi i kako ih koristiti unutar Bash skriptova kreirajući pet malih programa.",
        
        # Section 20
        "SQL, or Structured Query Language, is the language for communicating with a relational database. Bash is a Unix shell and command language.": "SQL, ili Structured Query Language, je jezik za komunikaciju sa relacionom bazom podataka. Bash je Unix školjka i komandni jezik.",
        "In this course, you will create a Bash script that uses SQL to enter information about your computer science students into a database.": "U ovom kursu, napravićeš Bash skript koji koristi SQL za unos informacija o studentima računarskih nauka u bazu podataka.",
        
        # Note translations
        "Note: Some browser extensions, such as ad-blockers and script-blockers can interfere with the tests. If you face issues, we recommend disabling extensions that modify the content or layout of pages, while taking the course.": "Napomena: Neka proširenja pregledača, kao što su blokatori oglasa i skripti mogu ometati testove. Ako naiđeš na probleme, preporučujemo da onemogućiš proširenja koja modifikuju sadržaj ili izgled stranica dok pohađaš kurs.",
        "Note: Some browser extensions, such as ad-blockers and dark mode extensions can interfere with the tests. If you face issues, we recommend disabling extensions that modify the content or layout of pages, while taking the course.": "Napomena: Neka proširenja pregledača, kao što su blokatori oglasa i ekstenzije za tamni režim mogu ometati testove. Ako naiđeš na probleme, preporučujemo da onemogućiš proširenja koja modifikuju sadržaj ili izgled stranica dok pohađaš kurs.",
        
        # Section 11 block titles
        "Learn String Manipulation by Building a Cipher": "Nauči Manipulaciju Stringovima Gradeći Šifru",
        "Learn How to Work with Numbers and Strings by Implementing the Luhn Algorithm": "Nauči Rad sa Brojevima i Stringovima Implementirajući Luhn Algoritam",
        "Learn Python List Comprehension by Building a Case Converter Program": "Nauči Python List Comprehension Gradeći Program za Konverziju Slova",
        "Learn Regular Expressions by Building a Password Generator": "Nauči Regularne Izraze Gradeći Generator Lozinki",
        "Learn Algorithm Design by Building a Shortest Path Algorithm": "Nauči Dizajn Algoritama Gradeći Algoritam Najkraćeg Puta",
        "Learn Recursion by Solving the Tower of Hanoi Puzzle": "Nauči Rekurziju Rešavajući Hanoi Kulu Puzzle",
        "Learn Data Structures by Building the Merge Sort Algorithm": "Nauči Strukture Podataka Gradeći Merge Sort Algoritam",
        "Learn Classes and Objects by Building a Sudoku Solver": "Nauči Klase i Objekte Gradeći Sudoku Rešavač",
        "Learn Tree Traversal by Building a Binary Search Tree": "Nauči Obilazak Stabla Gradeći Binarno Stablo Pretrage",
        "Learn Lambda Functions by Building an Expense Tracker": "Nauči Lambda Funkcije Gradeći Praćenje Troškova",
        "Build an Arithmetic Formatter Project": "Napravi Projekat Aritmetičkog Formatiranja",
        "Build a Time Calculator Project": "Napravi Projekat Kalkulatora Vremena",
        "Build a Budget App Project": "Napravi Projekat Aplikacije za Budžet",
        "Build a Polygon Area Calculator Project": "Napravi Projekat Kalkulatora Površine Poligona",
        "Build a Probability Calculator Project": "Napravi Projekat Kalkulatora Verovatnoće",
        "Learn Interfaces by Building an Equation Solver": "Nauči Interfejse Gradeći Rešavač Jednačina",
        "Learn Special Methods by Building a Vector Space": "Nauči Specijalne Metode Gradeći Vektorski Prostor",
        "Learn Encapsulation by Building a Projectile Trajectory Calculator": "Nauči Enkapsulaciju Gradeći Kalkulator Putanje Projektila",
        "Learn the Bisection Method by Finding the Square Root of a Number": "Nauči Metodu Bisekcije Nalazeći Kvadratni Koren Broja",
        
        # Section 5 block titles that are in English
        "Bootstrap": "Bootstrap",
        "jQuery": "jQuery",
        "SASS": "SASS",
        "React": "React",
        "Redux": "Redux",
        
        # Section 14 block titles
        "Searching Algorithms": "Algoritmi Pretrage",
        "Time Complexity": "Vremenska Složenost",
        "Algorithms in Code": "Algoritmi u Kodu",
        "Recursion and Space Complexity": "Rekurzija i Prostorna Složenost",
        "Introduction to Arrays": "Uvod u Nizove",
        "Introduction to Linked Lists": "Uvod u Povezane Liste",
        "Merge Sort Algorithm": "Merge Sort Algoritam",
        "Sorting a Linked List": "Sortiranje Povezane Liste",
        "Sorting Algorithms": "Algoritmi Sortiranja",
        "Searching Names using Sorting and Searching Algorithms": "Pretraga Imena koristeći Algoritme Sortiranja i Pretrage",
        
        # Section 15 block titles
        "Understanding RAG": "Razumevanje RAG",
        "Retrieval Engine Internals": "Unutrašnjost Retrieval Engine-a",
        "Designing Reliable RAG Systems": "Dizajniranje Pouzdanih RAG Sistema",
        "MCP Ecosystem & Tooling": "MCP Ekosistem i Alati",
        
        # Section 16 block titles
        "Function Basics": "Osnove Funkcija",
        "Angles and Circular Motion": "Uglovi i Kružno Kretanje",
        "Right Triangle Trigonometry": "Trigonometrija Pravouglog Trougla",
        "Trigonometric Graphs and Inverses": "Trigonometrijski Grafovi i Inverzne Funkcije",
        "Solving Trigonometric Equations": "Rešavanje Trigonometrijskih Jednačina",
        "Trigonometric Identities and Formulas": "Trigonometrijski Identiteti i Formule",
        "Advanced Trigonometry and Conics": "Napredna Trigonometrija i Konike",
        
        # Section 17 block titles
        "Understanding the Command Line and Working with Bash": "Razumevanje Komandne Linije i Rad sa Bash",
        "Build a Boilerplate": "Napravi Boilerplate",
        "Bash Commands Review": "Pregled Bash Komandi",
        "Bash Commands Quiz": "Kviz o Bash Komandama",
        
        # Section 18 block titles
        "Working with Relational Databases": "Rad sa Relacionim Bazama Podataka",
        "Build a Database of Video Game Characters": "Napravi Bazu Podataka Likova iz Video Igara",
        "Build a Celestial Bodies Database": "Napravi Bazu Podataka Nebeskih Tela",
        "SQL and PostgreSQL Review": "Pregled SQL i PostgreSQL",
        "SQL and PostgreSQL Quiz": "Kviz o SQL i PostgreSQL",
        
        # Section 19 block titles
        "Understanding Bash Scripting": "Razumevanje Bash Skriptovanja",
        "Build Five Programs": "Napravi Pet Programa",
        "Bash Scripting Review": "Pregled Bash Skriptovanja",
        "Bash Scripting Quiz": "Kviz o Bash Skriptovanju",
        
        # Section 20 block titles
        "Working With SQL": "Rad sa SQL",
        "Build a Student Database: Part 1": "Napravi Bazu Podataka Studenata: 1. Deo",
        "Build a Student Database: Part 2": "Napravi Bazu Podataka Studenata: 2. Deo",
        "Build a World Cup Database": "Napravi Bazu Podataka Svetskog Prvenstva",
        "Build a Kitty Ipsum Translator": "Napravi Kitty Ipsum Prevodioca",
        "Build a Bike Rental Shop": "Napravi Prodavnicu za Iznajmljivanje Bicikala",
        "Build a Salon Appointment Scheduler": "Napravi Zakazivač Termina za Salon",
        "Bash and SQL Review": "Pregled Bash i SQL",
        "Bash and SQL Quiz": "Kviz o Bash i SQL",
        
        # Section 3 - extra
        "Basic JavaScript": "Osnovni JavaScript",
        "ES6": "ES6",
        "Regular Expressions": "Regularni Izrazi",
        "Basic Data Structures": "Osnovne Strukture Podataka",
        "Basic Algorithm Scripting": "Osnovno Algoritamsko Skriptovanje",
        "Object Oriented Programming": "Objektno-Orijentisano Programiranje",
        "Functional Programming": "Funkcionalno Programiranje",
        "Intermediate Algorithm Scripting": "Naprednije Algoritamsko Skriptovanje",
        "JavaScript Algorithms and Data Structures Projects": "JavaScript Algoritmi i Strukture Podataka Projekti",
        "Utatuzi (Debugging)": "Debugovanje",
        
        # Section 4 - block titles
        "Build an RPG Creature Search App Project": "Napravi Projekat Aplikacije za Pretragu RPG Stvorenja",
        "Build a Cash Register Project": "Napravi Projekat Kase",
        "Build a Palindrome Checker Project": "Napravi Projekat Proveravača Palindroma",
        "Build a Roman Numeral Converter Project": "Napravi Projekat Konvertora Rimskih Brojeva",
        "Build a Telephone Number Validator Project": "Napravi Projekat Validatora Telefonskih Brojeva",
        "Learn Basic JavaScript by Building a Role Playing Game": "Nauči Osnovni JavaScript Gradeći IGRU Uloge",
        "Learn Form Validation by Building a Calorie Counter": "Nauči Validaciju Forme Gradeći Brojač Kalorija",
        "Learn Functional Programming by Building a Spreadsheet": "Nauči Funkcionalno Programiranje Gradeći Tabelu",
        "Learn Modern JavaScript Methods by Building Football Team Cards": "Nauči Moderne JavaScript Metode Gradeći Kartice Fudbalskog Tima",
        "Learn Advanced Array Methods by Building a Statistics Calculator": "Nauči Napredne Metode Nizova Gradeći Statistički Kalkulator",
        "Learn Basic OOP by Building a Shopping Cart": "Nauči Osnovni OOP Gradeći Korpu za Kupovinu",
        "Learn Fetch and Promises by Building an fCC Authors Page": "Nauči Fetch i Promise Gradeći fCC Stranicu Autora",
        "Learn Regular Expressions by Building a Spam Filter": "Nauči Regularne Izraze Gradeći Spam Filter",
        "Learn Basic Algorithmic Thinking by Building a Number Sorter": "Nauči Osnovno Algoritamsko Razmišljanje Gradeći Sortiranje Brojeva",
        "Review Algorithmic Thinking by Building a Dice Game": "Pregledaj Algoritamsko Razmišljanje Gradeći Igru Kockica",
        "Learn Intermediate OOP by Building a Platformer Game": "Nauči Intermediate OOP Gradeći Platformer Igru",
        "Learn localStorage by Building a Todo App": "Nauči localStorage Gradeći Todo Aplikaciju",
        "Learn the Date Object by Building a Date Formatter": "Nauči Date Objekat Gradeći Formatiranje Datuma",
        "Learn Asynchronous Programming by Building an fCC Forum Leaderboard": "Nauči Asinhrono Programiranje Gradeći fCC Forum Lider Tablu",
        "Learn Basic String and Array Methods by Building a Music Player": "Nauči Osnovne Metode Stringova i Nizova Gradeći Muzički Plejer",
        "Learn Recursion by Building a Decimal to Binary Converter": "Nauči Rekurziju Gradeći Konvertor Decimalnog u Binarni",
        "Learn Introductory JavaScript by Building a Pyramid Generator": "Nauči Uvodni JavaScript Gradeći Generator Piramide",
        "Review JavaScript Fundamentals by Building a Gradebook App": "Pregledaj JavaScript Osnove Gradeći Aplikaciju za Ocene",
        "Learn Basic Debugging by Building a Random Background Color Changer": "Nauči Osnovno Debugovanje Gradeći Menjač Nasumične Boje Pozadine",
        "Review DOM Manipulation by Building a Rock, Paper, Scissors Game": "Pregledaj DOM Manipulaciju Gradeći Igru Kamen, Papir, Makaze",
        
        # Section 7 block titles
        "Introduction to Data Visualization": "Uvod u Vizuelizaciju Podataka",
        "Build a Bar Chart": "Napravi Trakasti Grafikon",
        "Build a Scatterplot Graph": "Napravi Scatterplot Grafikon",
        
        # Section 13 block titles
        "Python Setup & First Steps": "Python Podešavanje i Prvi Koraci",
        "Core Primitives in Python": "Osnovni Primitivi u Python-u",
        "Small Python Projects": "Mali Python Projekti",
        "Lists and Tuples": "Liste i Tuple-ovi",
        "Control Flow and Functions": "Kontrola Toka i Funkcije",
        "Dictionaries and Loops": "Rečnici i Petlje",
        "Error Handling, Files, and Modules": "Rukovanje Greškama, Datoteke i Moduli",
        "Object-Oriented Programming with Python": "Objektno-Orijentisano Programiranje sa Python-om",
    }
    
    return translations.get(text, text)

def translate_value(val):
    """Recursively translate string values in the JSON structure."""
    if isinstance(val, str):
        return translate_text(val)
    elif isinstance(val, list):
        return [translate_value(item) for item in val]
    elif isinstance(val, dict):
        return {k: translate_value(v) for k, v in val.items()}
    else:
        return val

# Process only the first 20 sections
completed_sections = []
for i in range(20):
    key = keys[i]
    print(f"Processing {i+1}/20: {key}")
    data[key] = translate_value(data[key])
    completed_sections.append(key)

print("\n=== COMPLETED SECTIONS ===")
for i, section in enumerate(completed_sections, 1):
    print(f"{i}. {section}")

print(f"\nTotal processed: {len(completed_sections)} sections")

# Validate JSON by writing to string and parsing back
try:
    output = json.dumps(data, ensure_ascii=False, indent=2)
    json.loads(output)  # validate
    print("\n✅ JSON validation PASSED")
    print(f"Output size: {len(output)} characters")
    
    # Write to new file
    with open('client/i18n/locales/swahili/intro.json', 'w', encoding='utf-8') as f:
        f.write(output)
    print("✅ File written successfully")
    
except Exception as e:
    print(f"\n❌ JSON validation FAILED: {e}")
    sys.exit(1)