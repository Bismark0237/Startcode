# Import modules
from pathlib import Path
import json
from datetime import datetime, timedelta
from database_wrapper import Database

# Start werkdag tijd
START_TIJD = datetime.strptime("08:00", "%H:%M")

# Gesimuleerde weergegevens (zonder API-call)
def haal_weer_op():
    """Simuleert actuele weersgegevens zonder externe API."""
    return {
        "temperatuur": 15,  # Voorbeeldtemperatuur
        "weeromschrijving": "bewolkt",  # Voorbeeld weersbeschrijving
        "regen": False  # Simuleer geen regen
    }

def pas_taken_aan_op_weer(onderhoudstaken, weer):
    """Past onderhoudstaken aan op basis van het weer."""
    if weer and weer["regen"]:
        print("🌧 Regen verwacht! Buitenwerk wordt verminderd.")
        onderhoudstaken = [taak for taak in onderhoudstaken if not taak.get("is_buitenwerk", False)]
    return onderhoudstaken

def plan_pauzes(dagplanning, werktijd, pauze_opsplitsen):
    """Plant pauzes in het dagprogramma."""
    if werktijd > 330:  # Meer dan 5,5 uur werken
        if pauze_opsplitsen:
            dagplanning.append({"tijd": "TBD", "taak": "Pauze", "duur": 15})
            dagplanning.append({"tijd": "TBD", "taak": "Pauze", "duur": 15})
        else:
            dagplanning.append({"tijd": "TBD", "taak": "Pauze", "duur": 30})

def extra_pauze_bij_hitte(dagplanning, temperatuur):
    """Voegt een extra pauze toe als de temperatuur boven 30°C is."""
    if temperatuur > 30:
        dagplanning.append({"tijd": "TBD", "taak": "Extra pauze door hitte", "duur": 15})

def genereer_dagplanning(personeelslid, onderhoudstaken, weer):
    """Genereert een volledige dagplanning met weersinformatie, attracties, beroepstype, bevoegdheid en fysieke belasting."""
    max_werkduur = personeelslid.get("werktijd", 480)  # Max werkduur in minuten
    huidige_tijd = START_TIJD
    totale_duur = 0
    dagplanning = []
    onderhoudstaken = pas_taken_aan_op_weer(onderhoudstaken, weer)
    
    while totale_duur < max_werkduur:
        for taak in onderhoudstaken:
            if totale_duur >= max_werkduur:
                break
            taak_naam = taak.get("omschrijving", "Onbekend")
            taak_duur = taak.get("duur", 0)
            attractie = taak.get("attractie", "Geen attractie")
            fysieke_belasting = taak.get("fysieke_belasting", "Onbekend")
            tijdslot = huidige_tijd.strftime("%H:%M")
            
            dagplanning.append({
                "tijd": tijdslot,
                "taak": taak_naam,
                "duur": taak_duur,
                "attractie": attractie,
                "beroepstype": personeelslid.get("beroepstype", "Onbekend"),
                "bevoegdheid": personeelslid.get("bevoegdheid", "Onbekend"),
                "fysieke_belasting": fysieke_belasting,
                "weer": weer["weeromschrijving"] if weer else "Onbekend"
            })
            
            huidige_tijd += timedelta(minutes=taak_duur)
            totale_duur += taak_duur
    
    # Pauze toevoegen
    plan_pauzes(dagplanning, max_werkduur, personeelslid.get("pauze_opsplitsen", False))
    # Extra pauze bij hitte
    extra_pauze_bij_hitte(dagplanning, weer["temperatuur"])
    
    return dagplanning, totale_duur

def main():
    db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_onderhoud")
    db.connect()
    weer = haal_weer_op()
    
    naam = input("📂 Voer de naam van het personeelslid in: ").strip()
    bestand_pad = Path(__file__).parent / f'personeelsgegevens_{naam.replace(" ", "_")}.json'
    personeelsgegevens = json.load(open(bestand_pad))
    onderhoudstaken = db.execute_query("SELECT * FROM onderhoudstaak WHERE beroepstype = %s", (personeelsgegevens["beroepstype"],))
    
    dagplanning, totale_duur = genereer_dagplanning(personeelsgegevens, onderhoudstaken, weer)
    output_data = {
        "personeelsgegevens": personeelsgegevens,
        "dagtaken": dagplanning,
        "totale_duur": totale_duur,
        "weer": weer
    }
    uitvoer_pad = Path(__file__).parent / f'dagplanning_{naam.replace(" ", "_")}.json'
    
    with open(uitvoer_pad, 'w') as json_bestand_uitvoer:
        json.dump(output_data, json_bestand_uitvoer, indent=4)
    
    print(f"✅ Dagplanning opgeslagen in {uitvoer_pad}")
    db.close()

if __name__ == "__main__":
    main()
