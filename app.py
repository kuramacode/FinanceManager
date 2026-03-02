from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('main.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT)')
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchall()
        if user and user[0][1] == username:
            if user[0][2] == password:
                return f"Welcome back, {username}!"
        else:
            return "Invalid username or password."
    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_repeate = request.form['password_repeate']
        email = request.form['email']

        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT)')
        cur.execute('SELECT * FROM users WHERE username=? AND password=? AND password_repeate=? AND email=?', (username, password, password_repeate, email))
        user = cur.fetchall()
        

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
