from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import string
import random

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///url.db'
app.config['SECRET_KEY'] = 'secret_key'

db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(250), nullable=False)
    short_url = db.Column(db.String(10), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


with app.app_context():
    db.create_all()



def generate_short_url():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=6))



@app.route('/', methods=["GET", "POST"])
def home():

    if "user" not in session:
        return redirect('/login')

    if request.method == "POST":

        url = request.form['url']

        short_url = generate_short_url()

        new_url = URL(
            original_url=url,
            short_url=short_url,
            user_id=session['user']
        )

        db.session.add(new_url)
        db.session.commit()

        flash("URL shortened successfully!", "success")

    all_urls = URL.query.filter_by(user_id=session['user']).all()

    return render_template('index.html', all_urls=all_urls)



@app.route('/<short_url>')
def redirect_url(short_url):

    url = URL.query.filter_by(short_url=short_url).first()

    if url:
        return redirect(url.original_url)

    return "URL Not Found", 404



@app.route('/delete/<int:url_id>')
def delete_url(url_id):

    if "user" not in session:
        return redirect('/login')

    url = URL.query.filter_by(id=url_id).first()

    if url and url.user_id == session['user']:
        db.session.delete(url)
        db.session.commit()
        flash("URL deleted successfully.", "success")

    return redirect('/')



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        existing_user = User.query.filter_by(username=username).first()

        if not existing_user:

            new_user = User(
                username=username,
                password=hashed_password
            )

            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Please login.", "success")
            return redirect("/login")

        flash("Username already exists.", "danger")

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session['user'] = user.id

            flash("Login successful!", "success")

            return redirect("/")

        flash("Invalid username or password.", "danger")

    return render_template("login.html")



@app.route("/logout")
def logout():

    session.pop("user", None)

    flash("You have been logged out.", "info")

    return redirect("/login")



if __name__ == "__main__":
    app.run(debug=True)