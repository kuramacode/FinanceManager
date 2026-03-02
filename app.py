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
        
    return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_repeate = request.form['password_repeat']
        email = request.form['email']

        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT)')
        columns = [row[1] for row in cur.execute('PRAGMA table_info(users)')]
        if 'email' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN email TEXT')
        cur.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                    (username, password, email))
        cur.execute('SELECT * FROM users')
        conn.commit()
        conn.close()
        if password == password_repeate:
            return f"{username}, Successul adding!"

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
