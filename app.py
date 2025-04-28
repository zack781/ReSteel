from flask import Flask, render_template, redirect, url_for 
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host= 'localhost',
    user= 'root',
    password='',
    database="strucdb"
)

cursor = db.cursor(dictionary=True)

# Route: Welcome Page
@app.route('/')
def index():
    return render_template('index.html')

# Route: Boards Page (show all PNGs and DXFs)
@app.route('/boards')
def boards():
    cursor.execute("SELECT * FROM boards")
    boards_data = cursor.fetchall()
    return render_template('boards.html', boards=boards_data)

if __name__ == '__main__':
    app.run(debug=True)
