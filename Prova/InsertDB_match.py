from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
from collections import defaultdict


# Connessione al database
client = MongoClient("mongodb://localhost:27017/")
db = client["tipster_platform"]
matches_collection = db["matches_odds"]
matches_collection_results = db["matches_results"]
matches_collection_QuotaFinale = db["matches_odds_final"]


competition_names = matches_collection_results.distinct("competition_name")

#print("Campionati disponibili:", competition_names)

def inserDB_match():
    # Inserisci i dati nel database
    #print("Stiamo entrando")
    for campionato in competition_names:
        #print("Nome campionato:", campionato)
        eventCampionato = get_matchCompetition(campionato)
        #print("Eventi ottenuti:", eventCampionato)
        matches_collection_QuotaFinale.insert_many(eventCampionato.values())

def get_matchCompetition(campionati_selezionati):
    
    if campionati_selezionati:
        pipeline = [
            {"$match": {"competition_name": campionati_selezionati}},
            {"$sort": {"date_start": 1}}
        ]

        result = list(matches_collection.aggregate(pipeline))

        # Usa un dizionario per raggruppare i dati per 'match_id'
        match_data = defaultdict(list)

        # Popola il dizionario con i dati
        for item in result:
            match_id = item['match_id']
            match_data[match_id].append(item)

        # Crea un dizionario per memorizzare il miglior oggetto per ogni match_id
        best_odds = {}

        for match_id, odds_list in match_data.items():
            resultFinal = list(matches_collection_results.find({"match_id": match_id}))
            if not resultFinal:
                continue  # Nessun risultato trovato per questo match_id
            final_result = resultFinal[0]["final_result"]

            # Determina il migliore basato sul risultato finale
            if final_result == 'x':
                best_odd = max(odds_list, key=lambda x: x['tie_odd'])
            elif final_result == 1:
                best_odd = max(odds_list, key=lambda x: x['home_team_odd'])
            elif final_result == 2:
                best_odd = max(odds_list, key=lambda x: x['away_team_odd'])
            else:
                best_odd = None  # Risultato finale non valido

            if best_odd:
                best_odds[match_id] = best_odd
    return best_odds


inserDB_match()