from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import os
import random

# Percorso della directory delle immagini del profilo

# Recupera la lista dei file nell'elenco delle immagini del profilo


app = Flask(__name__)
app.secret_key = "supersecretkey"

client = MongoClient("mongodb://localhost:27017/")
db = client["tipster_platform"]
users_collection = db["users"]


@app.route("/Login", methods=["GET", "POST"])
def Login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({"username": email})

        if user:
            stored_password = user['password']
            if password == stored_password:
                flash("Login successful!", "success")
                return redirect(url_for("home"))
            else:
                flash("Invalid credentials, please try again.", "danger")
        else:
            flash("User not found, please register first.", "danger")

    return render_template("login.html")


@app.route("/Registration", methods=["GET", "POST"])
def Registration():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        name = request.form.get("name")

        print(email, password, role, name)

        # Check if user already exists
        if users_collection.find_one({"username": email}):
            flash("User already exists, please log in.", "warning")
            return redirect(url_for("Login"))

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


@app.route("/")
def home():
    tipster_users = db.users.find({"role": "tipster"})
    profile_images_list = os.listdir("./static/imageProfile/")
    return render_template('index.html', tipster_users=tipster_users, profile_images_list=profile_images_list)


@app.route('/profile')
def profile():
    return render_template('profile.html')


if __name__ == '__main__':
    app.run(debug=True)
