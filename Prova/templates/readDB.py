from pymongo import MongoClient

# Connessione al client MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["tipster_platform"]
matches_collection = db["matches_odds"]
results_collection = db["matches_results"]

campionati = [
    "Eng. Premier League"
]

def trova_quote_alte_per_campionati(campionati):
    # Filtra i documenti in matches_odds per i campionati specificati
    documenti_quote = list(matches_collection.find({"competition_name": {"$in": campionati}}))

    # Raggruppa i documenti per match_id
    match_ids = {doc["match_id"] for doc in documenti_quote}

    for match_id in match_ids:
        # Trova tutti i documenti per il match_id corrente
        documenti_quote_match = [doc for doc in documenti_quote if doc["match_id"] == match_id]
        
        # Trova tutti i documenti in matches_results per il match_id corrente
        documenti_risultati = list(results_collection.find({"match_id": match_id}))

        if not documenti_risultati:
            print(f"Nessun risultato trovato per match_id {match_id}")
            continue

        for risultato in documenti_risultati:
            final_result = risultato.get("final_result")
            if final_result == 1:
                # Trova il documento con home_team_odd massimo
                documento_max = max(
                    (doc for doc in documenti_quote_match if doc.get('home_team_odd') is not None),
                    key=lambda x: x.get('home_team_odd', 0)
                )
                print(f"Quote con final_result '1' per match_id {match_id}:", documento_max)
            elif final_result == 2:
                # Trova il documento con away_team_odd massimo
                documento_max = max(
                    (doc for doc in documenti_quote_match if doc.get('away_team_odd') is not None),
                    key=lambda x: x.get('away_team_odd', 0)
                )
                print(f"Quote con final_result '2' per match_id {match_id}:", documento_max)
            elif final_result == 0:  # Considerando 'x' come 0
                # Trova il documento con tie_odd massimo
                documento_max = max(
                    (doc for doc in documenti_quote_match if doc.get('tie_odd') is not None),
                    key=lambda x: x.get('tie_odd', 0)
                )
                print(f"Quote con final_result 'x' per match_id {match_id}:", documento_max)
            else:
                print(f"Final_result '{final_result}' non gestito per match_id {match_id}")

# Esempio di utilizzo della funzione per i campionati specificati
trova_quote_alte_per_campionati(campionati)
