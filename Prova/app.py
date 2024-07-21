from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
import os
import random
from bson.json_util import dumps
from datetime import datetime
from bson import ObjectId
from collections import defaultdict

# Percorso della directory delle immagini del profilo

# Recupera la lista dei file nell'elenco delle immagini del profilo

app = Flask(__name__)
app.secret_key = "supersecretkey"

client = MongoClient("mongodb://localhost:27017/")
db = client["tipster_platform"]
users_collection = db["users"]
matches_collection = db["matches_odds"]
matches_collection_results = db["matches_results"]
schedina = db["schedina"]

@app.route("/Login", methods=["GET", "POST"])
def Login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({"username": email})
        print("Utente", email, password)
        print("Utente1", user)
        if user:
            stored_password = user['password']
            if password == stored_password:
                session['user_id'] = email  # Memorizza l'ID dell'utente nella sessione
                return redirect(url_for("prova"))
            else:
                print("Password non corretta. Riprova.")
        else:
            print("Utente non trovato. Si prega di registrarsi prima.")

    return render_template("login.html")

"""
@app.route('/home')
def home():
    if 'user_id' in session:
        user_id = session['user_id']
        user = users_collection.find_one({'username': user_id})
        if user:
            return f"Welcome, {user['username']}!"
        else:
            logging.debug(f"User with id {user_id} not found.")
            return redirect(url_for('Login'))
    else:
        logging.debug("No user_id in session.")
    return redirect(url_for('Login'))



@app.route('/logout')
def logout():
    # Rimuovi l'ID utente dalla sessione
    session.pop('user_id', None)
    logging.debug("User logged out.")
    return redirect(url_for('Login'))

"""
@app.route("/Registration", methods=["GET", "POST"])
def Registration():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        name = request.form.get("name")

        print(email, password, role, name)

        existing_user  = users_collection.find_one({"username": email})
        # Check if user already exists
        if existing_user:
            flash("User already exists, please log in.", "warning")
            return redirect(url_for("Registration"))

        # Create a user object
        user = {
            "username": email,
            "password": password,  # This will be stored as a byte string
            "role": role,
            "name": name,
        }
        print("Oggetto da creare", user)
        # Insert the user into the database
        users_collection.insert_one(user)

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("Login"))

    return render_template("registration.html")


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    
    # Altri dati da passare al template
    distinct_competitions = matches_collection_results.distinct("competition_name")
    tipster_users = db.users.find({"role": "tipster"})
    profile_images_list = os.listdir("./static/imageProfile/")
    
    return render_template('homepage.html', 
                           tipster_users=tipster_users, 
                           profile_images_list=profile_images_list, 
                           distinct_competitions=distinct_competitions,)


@app.route('/prova', methods=['GET', 'POST'])
def prova():
    # Altri dati da passare al template
    distinct_competitions = matches_collection_results.distinct("competition_name")
    tipster_users = db.users.find({"role": "tipster"})
    profile_images_list = os.listdir("./static/imageProfile/")


    user_id = session.get('user_id')
    if user_id:
        user = users_collection.find_one({"username": user_id})
        if user:
            # Passa i dati dell'utente al template
            return render_template('prova.html', 
                           tipster_users=tipster_users, 
                           profile_images_list=profile_images_list, 
                           distinct_competitions=distinct_competitions,user=user)
    return redirect(url_for("Login"))  # Reindirizza al login se l'utente non è autenticato
    
    
@app.route("/logout")
def logout():
    session.pop('user_id', None)  # Rimuove 'user_id' dalla sessione
    return redirect(url_for("homepage"))



@app.route('/filtro_partite1', methods=['POST'])
def filtro_partite1():
    campionati_selezionati = request.form.getlist('championship')
    if campionati_selezionati:
        competition_name = campionati_selezionati[0]
        pipeline = [
            {"$match": {"competition_name": competition_name}},
            {"$group": {
                "_id": "$match_id",
                "match_id": {"$first": "$match_id"},
                "date_start": {"$first": {"$toDate": "$date_start"}},
                "home_team_name": {"$first": "$home_team_name"},
                "away_team_name": {"$first": "$away_team_name"},
                "home_team_odd": {"$first": "$home_team_odd"},
                "away_team_odd": {"$first": "$away_team_odd"},
                "tie_odd": {"$first": "$tie_odd"}
            }},
            {"$sort": {"date_start": 1}}
        ]
        
        result = list(matches_collection.aggregate(pipeline))
        session['matches'] = result  # Memorizza i match nella sessione
        return redirect(url_for('visualizza_partite'))  # Reindirizza alla pagina 'crea_schedina'
    
    return "Nessun campionato selezionato", 400



@app.route('/visualizza_partite', methods=['GET', 'POST'])
def visualizza_partite():
    if request.method == 'POST':
        match_id = request.form.get('match_id')
        user_id = session.get('user_id')
        # Qui gestisci la logica per interagire con l'evento selezionato
        return f"Match ID selezionato: {match_id}"
    
    # Ottieni i dati degli eventi dalla sessione
    user_id = session.get('user_id')  # Assumendo che l'ID utente sia memorizzato nella sessione
    matches = session.get('matches', [])
    return render_template('visualizza_partite.html', matches=matches, user_id=user_id)



def getMatchesResult(campionati):
    pipeline = [
    {"$match": {"competition_name": {"$in": campionati}}},
    {"$addFields": {
        "date_start": {
            "$dateFromString": {"dateString": "$date_start", "format": "%m/%d/%Y %H:%M"}
        }
    }},
    {"$group": {
        "_id": {"match_id": "$match_id", "competition_name": "$competition_name"},
        "match_id": {"$first": "$match_id"},
        "date_start": {"$first": "$date_start"},
        "home_team_name": {"$first": "$home_team_name"},
        "away_team_name": {"$first": "$away_team_name"},
        "home_team_score": {"$first": "$home_team_score"},
        "away_team_score": {"$first": "$away_team_score"},
        "final_result": {"$first": "$final_result"},  # Mantieni il risultato finale se necessario
        "competition_name": {"$first": "$competition_name"}
    }},
    {"$sort": {"date_start": 1}}  # Ordina per data in ordine crescente
]
    return list(matches_collection_results.aggregate(pipeline))

@app.route('/filtro_partite', methods=['POST'])
def filtro_partite():
    # Ricezione dei dati dal form
    campionati_selezionati = request.form.getlist('championship')
    over_under = request.form.get('overUnder')
    gol_nogol = request.form.get('GolNogol')
    # Estrai la stringa dalla lista
    campionamenti_selezionati_string = campionati_selezionati[0]

    # Dividi la stringa in una lista di nomi di campionati
    campionamenti_selezionati_list = [x.strip() for x in campionamenti_selezionati_string.split(',')]

    # Verifica il risultato
    
    # Stampa dei dati ricevuti
    print(f"Campionati selezionati: {campionati_selezionati}")
    print(f"Over/Under selezionato: {over_under}")
    print(f"Gol/NoGol selezionato: {gol_nogol}")
    print("ecco",gol_nogol,over_under)
    print(campionati_selezionati)
    # Verifica se over_under e gol_nogol sono entrambi None
    #if over_under is None and gol_nogol is None:
        # Estrai il primo campionato selezionato (supponendo che sia singolo per la redirect)
    if campionamenti_selezionati_list and over_under == "" and gol_nogol ==  "":
        # Esegui la tua query MongoDB aggregata con corretti operatori di aggregazione
        
        # Definisci la pipeline di aggregazione
         # Definisci la pipeline di aggregazione
        pipeline = [
        {"$match": {"competition_name": {"$in": campionamenti_selezionati_list}}},
        {"$addFields": {
            "date_start": {
                "$dateFromString": {"dateString": "$date_start", "format": "%m/%d/%Y %H:%M"}
            },
            "competition_name": "$competition_name"  # Aggiungi il nome del campionato ai risultati
        }},
        {"$group": {
            "_id": {"match_id": "$match_id", "competition_name": "$competition_name"},
            "match_id": {"$first": "$match_id"},
            "date_start": {"$first": "$date_start"},
            "home_team_name": {"$first": "$home_team_name"},
            "away_team_name": {"$first": "$away_team_name"},
            "home_team_odd": {"$first": "$home_team_odd"},
            "away_team_odd": {"$first": "$away_team_odd"},
            "tie_odd": {"$first": "$tie_odd"},
            "competition_name": {"$first": "$competition_name"}  # Mantieni il nome del campionato
        }},
        {"$sort": {"date_start": 1}}
    ]
        result = list(matches_collection.aggregate(pipeline))
        print("Risultato", result)
        return render_template('try.html',matches=result)
    elif campionamenti_selezionati_list and over_under == "over25" and gol_nogol == "":
        print("ci sono altri parametri", campionamenti_selezionati_list,over_under,gol_nogol)
        view = []
        result = getMatchesResult(campionamenti_selezionati_list)
        print(result)
        print("-----------")
        
        # Iterazione su ogni elemento della lista
        for match in result:
            # Accesso ai dati dell'elemento corrente
            match_id = match['_id']['match_id']
            competition_name = match['_id']['competition_name']
            date_start = match['date_start']
            home_team_name = match['home_team_name']
            away_team_name = match['away_team_name']
            home_team_score = match['home_team_score']
            away_team_score = match['away_team_score']
            final_result = match['final_result']

            # Stampa i dettagli dell'incontro
            print(f"Match ID: {match_id}")
            print(f"Competition: {competition_name}")
            print(f"Date Start: {date_start}")
            print(f"Home Team: {home_team_name}")
            print(f"Away Team: {away_team_name}")
            print(f"Home Team Score: {home_team_score}")
            print(f"Away Team Score: {away_team_score}")
            print(f"Final Result: {final_result}")
            print("-" * 40)  # Separatore tra gli incontri
 
            if home_team_score + away_team_score > 2:
                view.append({
                'home_team_name': home_team_name,
                'competition_name': competition_name,
                'away_team_name': away_team_name,
                'date_start': date_start,
                'finalResult': f"{home_team_score} - {away_team_score}",
            })
        return render_template("try1.html",matches = view)
    elif campionamenti_selezionati_list and over_under == "under25" and gol_nogol == "":
        view = []
        result = getMatchesResult(campionamenti_selezionati_list)
        # Iterazione su ogni elemento della lista
        for match in result:
            # Accesso ai dati dell'elemento corrente
            match_id = match['_id']['match_id']
            competition_name = match['_id']['competition_name']
            date_start = match['date_start']
            home_team_name = match['home_team_name']
            away_team_name = match['away_team_name']
            home_team_score = match['home_team_score']
            away_team_score = match['away_team_score']
            final_result = match['final_result']

            if home_team_score + away_team_score <= 2:
                view.append({
                'home_team_name': home_team_name,
                'competition_name': competition_name,
                'away_team_name': away_team_name,
                'date_start': date_start,
                'finalResult': f"{home_team_score} - {away_team_score}",
            })
        return render_template("try1.html",matches = view)
    elif campionamenti_selezionati_list and over_under == "over25" and gol_nogol == "Gol":
        view = []
        result = getMatchesResult(campionamenti_selezionati_list)
        # Iterazione su ogni elemento della lista
        for match in result:
            # Accesso ai dati dell'elemento corrente
            match_id = match['_id']['match_id']
            competition_name = match['_id']['competition_name']
            date_start = match['date_start']
            home_team_name = match['home_team_name']
            away_team_name = match['away_team_name']
            home_team_score = match['home_team_score']
            away_team_score = match['away_team_score']
            final_result = match['final_result']

            if home_team_score + away_team_score > 2 and home_team_score > 0 and away_team_score > 0:
                view.append({
                'home_team_name': home_team_name,
                'competition_name': competition_name,
                'away_team_name': away_team_name,
                'date_start': date_start,
                'finalResult': f"{home_team_score} - {away_team_score}",
            })
        return render_template("try1.html",matches = view)
    elif campionamenti_selezionati_list and over_under == "over25" and gol_nogol == "NoGol":
        view = []
        result = getMatchesResult(campionamenti_selezionati_list)
        # Iterazione su ogni elemento della lista
        for match in result:
            # Accesso ai dati dell'elemento corrente
            match_id = match['_id']['match_id']
            competition_name = match['_id']['competition_name']
            date_start = match['date_start']
            home_team_name = match['home_team_name']
            away_team_name = match['away_team_name']
            home_team_score = match['home_team_score']
            away_team_score = match['away_team_score']
            final_result = match['final_result']

            if home_team_score == 0 or away_team_score == 0:
                if home_team_score + away_team_score > 2:
                    view.append({
                    'home_team_name': home_team_name,
                    'competition_name': competition_name,
                    'away_team_name': away_team_name,
                    'date_start': date_start,
                    'finalResult': f"{home_team_score} - {away_team_score}",
                })
        return render_template("try1.html",matches = view)
    elif campionamenti_selezionati_list and over_under == "under25" and gol_nogol == "Gol":
        view = []
        result = getMatchesResult(campionamenti_selezionati_list)
        # Iterazione su ogni elemento della lista
        for match in result:
            # Accesso ai dati dell'elemento corrente
            match_id = match['_id']['match_id']
            competition_name = match['_id']['competition_name']
            date_start = match['date_start']
            home_team_name = match['home_team_name']
            away_team_name = match['away_team_name']
            home_team_score = match['home_team_score']
            away_team_score = match['away_team_score']
            final_result = match['final_result']

            if home_team_score + away_team_score <= 2 and home_team_score > 0 and away_team_score > 0:
                view.append({
                'home_team_name': home_team_name,
                'competition_name': competition_name,
                'away_team_name': away_team_name,
                'date_start': date_start,
                'finalResult': f"{home_team_score} - {away_team_score}",
            })
        return render_template("try1.html",matches = view)
    elif campionamenti_selezionati_list and over_under == "under25" and gol_nogol == "NoGol":
        view = []
        result = getMatchesResult(campionamenti_selezionati_list)
        # Iterazione su ogni elemento della lista
        for match in result:
            # Accesso ai dati dell'elemento corrente
            match_id = match['_id']['match_id']
            competition_name = match['_id']['competition_name']
            date_start = match['date_start']
            home_team_name = match['home_team_name']
            away_team_name = match['away_team_name']
            home_team_score = match['home_team_score']
            away_team_score = match['away_team_score']
            final_result = match['final_result']

            if home_team_score == 0 or away_team_score == 0:
                if home_team_score + away_team_score <= 2:
                    view.append({
                    'home_team_name': home_team_name,
                    'competition_name': competition_name,
                    'away_team_name': away_team_name,
                    'date_start': date_start,
                    'finalResult': f"{home_team_score} - {away_team_score}",
                })
        return render_template("try1.html",matches = view)
    elif campionamenti_selezionati_list and over_under == "" and gol_nogol == "Gol":
        print("ci sono altri parametri", campionamenti_selezionati_list,over_under,gol_nogol)
        view = []
        result = getMatchesResult(campionamenti_selezionati_list)
        # Iterazione su ogni elemento della lista
        for match in result:
            # Accesso ai dati dell'elemento corrente
            match_id = match['_id']['match_id']
            competition_name = match['_id']['competition_name']
            date_start = match['date_start']
            home_team_name = match['home_team_name']
            away_team_name = match['away_team_name']
            home_team_score = match['home_team_score']
            away_team_score = match['away_team_score']
            final_result = match['final_result']
 
            if home_team_score > 0 and  away_team_score > 0:
                view.append({
                'home_team_name': home_team_name,
                'competition_name': competition_name,
                'away_team_name': away_team_name,
                'date_start': date_start,
                'finalResult': f"{home_team_score} - {away_team_score}",
            })
        return render_template("try1.html",matches = view)
    elif campionamenti_selezionati_list and over_under == "" and gol_nogol == "NoGol":
        print("ci sono altri parametri", campionamenti_selezionati_list,over_under,gol_nogol)
        view = []
        result = getMatchesResult(campionamenti_selezionati_list)
        # Iterazione su ogni elemento della lista
        for match in result:
            # Accesso ai dati dell'elemento corrente
            match_id = match['_id']['match_id']
            competition_name = match['_id']['competition_name']
            date_start = match['date_start']
            home_team_name = match['home_team_name']
            away_team_name = match['away_team_name']
            home_team_score = match['home_team_score']
            away_team_score = match['away_team_score']
            final_result = match['final_result']

 
            if home_team_score == 0 or away_team_score == 0:
                view.append({
                'home_team_name': home_team_name,
                'competition_name': competition_name,
                'away_team_name': away_team_name,
                'date_start': date_start,
                'finalResult': f"{home_team_score} - {away_team_score}",
            })
        return render_template("try1.html",matches = view)





@app.route('/get_matches')
def get_matches():
    # Paginazione
    page = request.args.get('page', 1, type=int)  # Ottieni il numero di pagina dalla query string, default a 1
    per_page = request.args.get('per_page', 5, type=int)  # Numero di elementi per pagina, default a 5

    start = (page - 1) * per_page

    # Esegui la tua query MongoDB aggregata con corretti operatori di aggregazione
    pipeline = [
        {"$match": {"competition_name": "Eng. Premier League"}},
        {"$group": {
            "_id": "$match_id",
            "match_id": {"$first": "$match_id"},
            "date_start": {"$first": {"$toDate": "$date_start"}},  # Converti a data
            "home_team_name": {"$first": "$home_team_name"},
            "away_team_name": {"$first": "$away_team_name"},
            "home_team_odd": {"$first": "$home_team_odd"},
            "away_team_odd": {"$first": "$away_team_odd"},
            "tie_odd": {"$first": "$tie_odd"}
        }},
        {"$sort": {"date_start": 1}}  # Ordina per data in ordine crescente
    ]

    # Esegui la query e ottieni il cursore dei risultati
    cursor = matches_collection.aggregate(pipeline)

    # Trasforma il cursore in una lista di documenti
    matches = list(cursor)

    # Applica la paginazione sui risultati ottenuti
    paginated_matches = matches[start:start + per_page]

    # Converti le date da datetime a stringa per renderle nel template
    for match in paginated_matches:
        match['date_start'] = match['date_start'].strftime('%Y-%m-%d %H:%M:%S')

    # Se la richiesta è AJAX, restituisci i dati in formato JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'matches': paginated_matches, 'page': page, 'per_page': per_page})

    # Altrimenti, renderizza il template HTML con i dati
    return render_template('try1.html', matches=paginated_matches, page=page, per_page=per_page)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.json
    user_id = data.get('userId')
    cart_items = data.get('cartItems', [])
    cart = session.get('cart', [])
    cart_id = str(ObjectId())

    for item in cart_items:
        match_id = item.get('matchId')
        odd_type = item.get('oddType')
        odd_value = item.get('oddValue')
        is_selected = item.get('isSelected', False)

        # Aggiorna il carrello nella sessione
        if is_selected:
            cart = [i for i in cart if i['matchId'] != match_id]
        else:
            cart.append({'matchId': match_id, 'oddType': odd_type})

        print("id match",match_id)
        match_schedina = matches_collection.find_one({"match_id": match_id})
        print(match_schedina)

        # Estrai i dati desiderati
        competition_name = match_schedina['competition_name']
        date_start = match_schedina['date_start']
        home_team_name = match_schedina['home_team_name']
        away_team_name = match_schedina['away_team_name']

        stringMatch = str(match_id)
        print("MatchString", stringMatch)
        # Crea il nuovo documento da inserire nella collezione schedina
        documento_schedina = {
            'user_id': user_id,
            'cart_id': cart_id,
            'match_id': stringMatch,
            'competition_name': competition_name,
            'date_start': date_start,
            'home_team_name': home_team_name,
            'away_team_name': away_team_name,
            'odd_type': odd_type,
            'odd_value': odd_value
        }

        schedina.insert_one(documento_schedina)

        print("Match_schedina", match_schedina)
        # Salva le schedine nel database
        #schedina = Schedina(user_id=user_id, match_id=match_id, odd_type=odd_type)
        #db.session.add(schedina)

    #db.session.commit()
    session['cart'] = cart

    #print("Schedine in generale\n", session['cart'])
    print("Sessione dell'utente", user_id)
    return jsonify({'message': 'Operazione completata'})


@app.route('/add_to_cartUtente', methods=['POST'])
def add_to_cartUtente():
    data = request.json
    user_id = data.get('userId')
    cart_items = data.get('cartItems', [])
    print("user della sessione", user_id)
    cart = session.get('cart', [])

    print(cart_items)
    cart_id_1 = str(ObjectId())
    print("card id", cart_id_1)
    cart_id = cart_items[0]['idSchedina']
    print("porco", cart_id)
    match_schedina = list(schedina.find({"cart_id": cart_id}))

    print("Schedine ottenute ----", match_schedina)

    for x in match_schedina:
            # Estrai i dati desiderati
        competition_name = x['competition_name']
        match_id = x['match_id']
        date_start = x['date_start']
        home_team_name = x['home_team_name']
        away_team_name = x['away_team_name']
        oddValue = x['odd_value']
        odd_type = x['odd_type']
        print(x, "----------")

        print("comp", competition_name)
        print("date", date_start)
        print("home", home_team_name)
        print("away", away_team_name)
        print("oddValue", oddValue)


            # Crea il nuovo documento da inserire nella collezione schedina
        documento_schedina = {
            'user_id': user_id,
            'cart_id': cart_id_1,
            'match_id': match_id,
            'competition_name': competition_name,
            'date_start': date_start,
            'home_team_name': home_team_name,
            'away_team_name': away_team_name,
            'odd_type': odd_type,
            'odd_value': oddValue
        }

        if not match_schedina:
            return jsonify({'message': 'Match non trovato'}), 404
        schedina.insert_one(documento_schedina)    
        
        # Aggiorna il carrello nella sessione
        cart.append({'matchId': match_id, 'oddType': odd_type})
    session['cart'] = cart

    return jsonify({'message': 'Operazione completata'})



# Route per ottenere i dettagli di un evento basato sul match_id
@app.route('/event/<int:match_id>', methods=['GET'])
def get_event(match_id):
    event = matches_collection.find_one({'match_id': match_id})
    if event:
        # Rimuovi il campo ObjectId (_id) se lo stai ritornando come parte dell'oggetto
        event.pop('_id', None)
        return jsonify(event)
    return jsonify({'error': 'Evento non trovato'}), 404

@app.route('/crea_schedina')
def crea_schedina():
    if 'user_id' not in session:
        return redirect(url_for('Login'))  # Reindirizza alla pagina di login se l'utente non è loggato
    
    distinct_competitions = matches_collection_results.distinct("competition_name")
    user_id = session.get('user_id')  # Recupera l'ID utente dalla sessione
    matches = session.get('matches', [])  # Recupera i match dalla sessione
    return render_template('crea_schedina.html', distinct_competitions=distinct_competitions, user_id=user_id, matches=matches)

@app.route('/profilo/<username>')
def profilo(username):
    
    user_id = session.get('user_id')
    print("Utente loggato", username)

    scommesse = list(schedina.find({"user_id": username}))

    # Dizionario per raggruppare le schedine per cart_id
    schedine_raggruppate = defaultdict(list)

    # Raggruppa le schedine per cart_id
    for scommessa in scommesse:
        schedine_raggruppate[scommessa['cart_id']].append(scommessa)

    # Trasforma il dizionario in una lista di liste (una lista per ogni gruppo di schedine)
    schedine_raggruppate = list(schedine_raggruppate.values())

    print(schedine_raggruppate)
    # Cerca l'utente nel database MongoDB
    user_data = users_collection.find_one({'username': username})
    user_data_Session = users_collection.find_one({'username': user_id})

    print("Utente", user_id, "Utente1", user_data_Session)

    if user_id is None:
        # Passa i dati all'HTML
        return render_template('profilo3.html', user=user_data, schedine=schedine_raggruppate)
    elif user_id == user_data["username"] and user_data["role"] == "tipster":
        print("perche sono qui")
        return render_template('profilo.html', user=user_data, schedine=schedine_raggruppate)
    elif user_id == username and user_data_Session["role"] == "giocatore":
        print("sono qui")
        return render_template('profilo1.html', user=user_data_Session, schedine=schedine_raggruppate)
    elif user_id != username and user_data_Session["role"] == "tipster":
        return render_template('profilo3.html', user=user_data, schedine=schedine_raggruppate)
    elif user_id != username and user_data_Session["role"] == "giocatore":
        print("non dovrei essere qui", user_id)
        return render_template('profilo2.html', user=user_data_Session, schedine=schedine_raggruppate)

@app.route('/elimina_scommessa/<scommessa_id>', methods=['DELETE'])
def elimina_scommessa(scommessa_id):

    print("id scommessa da cancellare", scommessa_id)

    try:
        result = schedina.delete_one({'match_id': scommessa_id})
        if result.deleted_count > 0:
            return jsonify({'message': 'Scommessa eliminata con successo.'}), 200
        else:
            return jsonify({'message': 'Scommessa non trovata.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/verifica_giocata', methods=['POST'])
def verifica_giocata():
    data = request.json
    cart_id = data.get('cartId')
    cart_items = data.get('cartItems', [])
    
    results = []
    
    print(cart_items)


    for item in cart_items:
        match_id = item.get('matchId')
        odd_type = item.get('oddType')

        print("Match_id", match_id)

        # Supponiamo di avere una funzione per verificare i risultati
        match = matches_collection_results.find_one({"match_id": int(match_id)})
        print(match)
        if match:
            result = match.get('final_result')  # Ad esempio, il risultato del match
            is_correct = (result == odd_type)
            results.append({
                'matchId': match_id,
                'Esito Predetto': odd_type,
                'Risultato Finale': result,
                'correct': is_correct
            })
    
    return jsonify(results)


@app.route('/rimuovi_schedina/<cart_id>', methods=['DELETE'])
def rimuovi_schedina(cart_id):
    print("id della schedina", cart_id)
    result = schedina.delete_many({"cart_id": cart_id})
    if result.deleted_count > 0:
        return jsonify({'success': True, 'message': 'Schedina rimossa con successo!'})
    else:
        return jsonify({'success': False, 'message': 'Schedina non trovata o già rimossa.'}), 404


@app.route('/search_tipster')
def search_tipster():
    query = request.args.get('q', '')
    if query:
        # Cerca gli utenti il cui username inizia con i caratteri della query
        results = users_collection.find({'username': {'$regex': f'^{query}', '$options': 'i'}})
        return dumps(results)
    return jsonify([])


if __name__ == '__main__':
    app.run(debug=True)
