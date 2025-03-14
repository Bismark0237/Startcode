# Import modules
from pathlib import Path
import json
import pprint
from datetime import datetime, timedelta
from database_wrapper import Database

# Start werkdag tijd
START_TIJD = datetime.strptime("08:00", "%H:%M")

# Functie om JSON-bestand in te lezen
def lees_personeelsgegevens(bestandspad):
    """Leest een JSON-bestand met personeelsgegevens in."""
    try:
        with open(bestandspad, 'r') as json_bestand:
            return json.load(json_bestand)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Fout: Kan JSON niet laden ({e})")
        return None

# Functie om een nieuw personeelslid aan te maken
def maak_personeelslid():
    """Vraagt gegevens van een nieuw personeelslid en slaat deze op in een JSON-bestand."""
    naam = input("👤 Voer de naam van het personeelslid in: ").strip()
    beroepstype = input("🔧 Voer de functie in (bijv. Mechanisch Monteur, Elektrisch Monteur): ").strip()
    bevoegdheid = input("🎓 Voer de bevoegdheid in (Junior, Medior, Senior, Stagiair): ").strip()
    max_werkduur = input("⏳ Voer de maximale werkduur in uren in (standaard = 8): ").strip()
    
    try:
        max_werkduur = int(max_werkduur) * 60  # Omzetten naar minuten
    except ValueError:
        print("⚠ Ongeldige invoer! Standaard werkduur van 8 uur wordt gebruikt.")
        max_werkduur = 8 * 60

    specialist_in_attracties = input("🎢 Voer specialisaties in attracties in, gescheiden door komma’s (of laat leeg): ").strip().split(",")

    if specialist_in_attracties == [""]:
        specialist_in_attracties = []

    personeelslid = {
        "naam": naam,
        "werktijd": max_werkduur,
        "beroepstype": beroepstype,
        "bevoegdheid": bevoegdheid,
        "specialist_in_attracties": specialist_in_attracties,
        "pauze_opsplitsen": False,
        "max_fysieke_belasting": 30
    }

    bestandspad = Path(__file__).parent / f'personeelsgegevens_{naam.replace(" ", "_")}.json'

    with open(bestandspad, 'w') as json_bestand:
        json.dump(personeelslid, json_bestand, indent=4)

    print(f"✅ Personeelslid '{naam}' aangemaakt en opgeslagen in {bestandspad}")
    return bestandspad

# Functie om onderhoudstaken op te halen
def haal_onderhoudstaken_op(db, personeelslid):
    """Haalt onderhoudstaken op uit de database op basis van beroepstype en bevoegdheid."""
    if not personeelslid:
        print("❌ Geen personeelsgegevens ontvangen!")
        return []

    beroep = personeelslid.get("beroepstype", "").strip()
    bevoegdheid = personeelslid.get("bevoegdheid", "").strip()

    if not beroep or not bevoegdheid:
        print("❌ Fout: Beroepstype of bevoegdheid ontbreekt!")
        return []

    select_query = """
        SELECT omschrijving, duur, prioriteit, beroepstype, bevoegdheid, fysieke_belasting, attractie, is_buitenwerk
        FROM onderhoudstaak 
        WHERE beroepstype = %s AND bevoegdheid = %s 
        ORDER BY prioriteit DESC, duur ASC
    """

    print(f"🔍 Uitvoeren SQL-query met parameters: {beroep}, {bevoegdheid}")

    try:
        onderhoudstaken = db.execute_query(select_query, (beroep, bevoegdheid))
    except Exception as e:
        print(f"❌ Fout bij uitvoeren van query: {e}")
        onderhoudstaken = []

    if not onderhoudstaken:
        print(f"⚠ Geen onderhoudstaken gevonden voor functie: {beroep} met bevoegdheid: {bevoegdheid}")
    
    return onderhoudstaken

# Functie om een dagplanning te genereren
def genereer_dagplanning(personeelslid, onderhoudstaken):
    """Genereert een volledige dagplanning en slaat deze op als JSON."""
    max_werkduur = personeelslid.get("werktijd", 480)  # Max werkduur in minuten
    huidige_tijd = START_TIJD
    totale_duur = 0
    dagplanning = []

    if not onderhoudstaken:
        print("⚠ Geen taken gevonden! Gebruik fallback-taken.")
        onderhoudstaken = [
            {"omschrijving": "Controle gereedschap", "duur": 30, "prioriteit": "Laag"},
            {"omschrijving": "Opruimen werkplek", "duur": 15, "prioriteit": "Laag"},
            {"omschrijving": "Routine inspectie", "duur": 45, "prioriteit": "Laag"}
        ]

    while totale_duur < max_werkduur:
        for taak in onderhoudstaken:
            if totale_duur >= max_werkduur:
                break  # Stop als de werktijd vol is
            
            taak_naam = taak.get("omschrijving", "Onbekend")
            taak_duur = taak.get("duur", 0)
            taak_prioriteit = taak.get("prioriteit", "Onbekend")
            attractie = taak.get("attractie", "Geen")
            fysieke_belasting = taak.get("fysieke_belasting", "Onbekend")
            buitenwerk = "Ja" if taak.get("is_buitenwerk", 0) else "Nee"

            tijdslot = huidige_tijd.strftime("%H:%M")
            dagplanning.append({
                "tijd": tijdslot,
                "taak": taak_naam,
                "duur": taak_duur,
                "prioriteit": taak_prioriteit,
                "beroepstype": personeelslid["beroepstype"],
                "bevoegdheid": personeelslid["bevoegdheid"],
                "attractie": attractie,
                "fysieke_belasting": fysieke_belasting,
                "buitenwerk": buitenwerk
            })

            huidige_tijd += timedelta(minutes=taak_duur)
            totale_duur += taak_duur

    print(f"✅ Dagplanning gegenereerd. Totaal geplande tijd: {totale_duur} minuten")
    
    return dagplanning, totale_duur

# Hoofdprogramma
def main():
    db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_onderhoud")
    db.connect()

    print("🌟 Welkom bij het personeelsbeheer van Attractiepark Lake Side Mania!")
    keuze = input("Wil je een nieuw personeelslid aanmaken? (ja/nee): ").strip().lower()

    if keuze == "ja":
        bestand_pad = maak_personeelslid()
    else:
        naam = input("📂 Voer de naam van het personeelslid in om de taken op te halen: ").strip()
        bestand_pad = Path(__file__).parent / f'personeelsgegevens_{naam.replace(" ", "_")}.json'
    
    personeelsgegevens = lees_personeelsgegevens(bestand_pad)

    if personeelsgegevens:
        onderhoudstaken = haal_onderhoudstaken_op(db, personeelsgegevens)
        dagplanning, totale_duur = genereer_dagplanning(personeelsgegevens, onderhoudstaken)

        output_data = {"personeelsgegevens": personeelsgegevens, "dagtaken": dagplanning, "totale_duur": totale_duur}

        uitvoer_pad = Path(__file__).parent / f'dagplanning_{personeelsgegevens["naam"].replace(" ", "_")}.json'
        with open(uitvoer_pad, 'w') as json_bestand_uitvoer:
            json.dump(output_data, json_bestand_uitvoer, indent=4)

        print(f"✅ Dagplanning opgeslagen in {uitvoer_pad}")

    db.close()

if __name__ == "__main__":
    main()
