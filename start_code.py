# Import modules
from pathlib import Path
import json
import pprint
from datetime import datetime, timedelta
from database_wrapper import Database

# Initialisatie databaseconnectie
db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_onderhoud")

# Start- en eindtijd werkdag
START_TIJD = datetime.strptime("08:00", "%H:%M")  # Start werkdag om 08:00
EIND_TIJD = datetime.strptime("17:00", "%H:%M")   # Eind werkdag om 17:00

# Functie om JSON-bestand in te lezen
def lees_personeelsgegevens(bestandspad):
    """Leest een JSON-bestand met personeelsgegevens in."""
    try:
        with open(bestandspad, 'r') as json_bestand:
            return json.load(json_bestand)
    except FileNotFoundError:
        print(f"❌ Fout: Het bestand {bestandspad} is niet gevonden!")
        return None
    except json.JSONDecodeError:
        print(f"❌ Fout: Ongeldig JSON-formaat in {bestandspad}!")
        return None

# Functie om een nieuw personeelslid aan te maken
def maak_personeelslid():
    """Vraagt gegevens van een nieuw personeelslid en slaat deze op in een JSON-bestand."""
    naam = input("👤 Voer de naam van het personeelslid in: ").strip()
    functie = input("🔧 Voer de functie in (bijv. Elektrisch Monteur, Mechanisch Monteur, Schilder, Onderhoudsmonteur): ").strip()
    bevoegdheid = input("🎓 Voer de bevoegdheid in (Junior, Medior, Senior, Stagiair): ").strip()
    max_werkduur = input("⏳ Voer de maximale werkduur in uren in (standaard = 8): ").strip()

    try:
        max_werkduur = int(max_werkduur) * 60  # Omzetten naar minuten
    except ValueError:
        print("⚠ Ongeldige invoer! Standaard werkduur van 8 uur wordt gebruikt.")
        max_werkduur = 8 * 60

    personeelslid = {
        "naam": naam,
        "functie": functie,
        "bevoegdheid": bevoegdheid,
        "max_werkduur": max_werkduur
    }

    bestandspad = Path(__file__).parent / f'personeelsgegevens_{naam.replace(" ", "_")}.json'

    with open(bestandspad, 'w') as json_bestand:
        json.dump(personeelslid, json_bestand, indent=4)

    print(f"✅ Personeelslid '{naam}' aangemaakt en opgeslagen in {bestandspad}")
    return bestandspad

# Functie om onderhoudstaken op te halen op basis van beroepstype en bevoegdheid
def haal_onderhoudstaken_op(personeelslid):
    """Haalt onderhoudstaken op uit de database op basis van beroepstype en bevoegdheid."""
    if not personeelslid:
        print("❌ Geen personeelsgegevens ontvangen!")
        return []

    db.connect()
    
    beroep = personeelslid.get("functie", "").strip()
    bevoegdheid = personeelslid.get("bevoegdheid", "").strip()

    select_query = """
        SELECT * FROM onderhoudstaak 
        WHERE beroepstype = %s AND bevoegdheid = %s 
        ORDER BY prioriteit DESC, duur ASC
    """

    print(f"🔎 SQL Query: {select_query} - Parameters: {beroep}, {bevoegdheid}")

    try:
        onderhoudstaken = db.execute_query(select_query, (beroep, bevoegdheid))
    except Exception as e:
        print(f"❌ Fout bij uitvoeren van query: {e}")
        onderhoudstaken = []

    db.close()
    
    if not onderhoudstaken:
        print(f"⚠ Geen onderhoudstaken gevonden voor functie: {beroep} met bevoegdheid: {bevoegdheid}")
    
    return onderhoudstaken

# Functie om een dagplanning te genereren
def genereer_dagplanning(personeelslid, onderhoudstaken):
    """Genereert een dagplanning met taken en pauzes."""
    max_werkduur = personeelslid.get("max_werkduur", 8 * 60)  # Max werkduur in minuten
    huidige_tijd = START_TIJD
    totale_duur = 0
    dagplanning = []

    print(f"🔎 Start werkdag: {huidige_tijd.strftime('%H:%M')}")
    print(f"🔎 Max werkduur: {max_werkduur} minuten")
    print(f"🔎 Onderhoudstaken gevonden: {len(onderhoudstaken)}")

    for taak in onderhoudstaken:
        taak_naam = taak.get("omschrijving", "Onbekend")
        taak_duur = taak.get("duur", 0)  # Zorg dat je een 'duur' veld hebt in je database
        attractie = taak.get("attractie", "Algemeen")
        fysieke_belasting = taak.get("fysieke_belasting", 0)
        buitenwerk = "Ja" if taak.get("is_buitenwerk", 0) else "Nee"

        if totale_duur + taak_duur > max_werkduur:
            break  # Stop als werkduur is bereikt

        tijdslot = huidige_tijd.strftime("%H:%M")
        dagplanning.append({
            "tijd": tijdslot,
            "taak": taak_naam,
            "duur": taak_duur,
            "attractie": attractie,
            "fysieke_belasting": fysieke_belasting,
            "buitenwerk": buitenwerk
        })

        # Update de huidige tijd en totale duur
        huidige_tijd += timedelta(minutes=taak_duur)
        totale_duur += taak_duur

    # Voeg pauzes toe
    pauzes = [
        {"tijd": "10:00", "taak": "Korte pauze", "duur": 15},
        {"tijd": "12:30", "taak": "Lunchpauze", "duur": 30},
        {"tijd": "15:00", "taak": "Korte pauze", "duur": 15}
    ]
    dagplanning.extend(pauzes)

    print(f"✅ Dagplanning gegenereerd. Totaal aantal werkminuten: {totale_duur}")
    
    return dagplanning

# Hoofdprogramma
def main():
    print("🌟 Welkom bij het personeelsbeheer van Attractiepark Lake Side Mania!")
    keuze = input("Wil je een nieuw personeelslid aanmaken? (ja/nee): ").strip().lower()

    if keuze == "ja":
        bestand_pad = maak_personeelslid()
    else:
        naam = input("📂 Voer de naam van het personeelslid in om de taken op te halen: ").strip()
        bestand_pad = Path(__file__).parent / f'personeelsgegevens_{naam.replace(" ", "_")}.json'
    
    # Lees personeelsgegevens
    personeelsgegevens = lees_personeelsgegevens(bestand_pad)

    if personeelsgegevens:
        # Haal onderhoudstaken op
        onderhoudstaken = haal_onderhoudstaken_op(personeelsgegevens)

        # Genereer dagplanning
        dagplanning = genereer_dagplanning(personeelsgegevens, onderhoudstaken)

        # Opslaan in JSON-bestand
        uitvoer_pad = Path(__file__).parent / f'dagplanning_{personeelsgegevens["naam"].replace(" ", "_")}.json'
        with open(uitvoer_pad, 'w') as json_bestand_uitvoer:
            json.dump(dagplanning, json_bestand_uitvoer, indent=4)

        print(f"✅ Dagplanning opgeslagen in {uitvoer_pad}")

if __name__ == "__main__":
    main()
