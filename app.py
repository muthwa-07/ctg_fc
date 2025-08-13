from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql

app = Flask(__name__)

# SQLAlchemy config for matches
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///matches.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Match model
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_result = db.Column(db.String(50))
    match_lineup = db.Column(db.Text)
    date = db.Column(db.Date)
    match_location = db.Column(db.String(100))
    match_time = db.Column(db.String(10))


# Redirect root to login
@app.route('/')
def home():
    return redirect(url_for('login'))


# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        jersey = request.form["jersey"]
        name = request.form["name"]

        connection = pymysql.connect(host="localhost", user="root", password="", database="ctg_fc")
        cursor = connection.cursor()

        sql = "SELECT * FROM player WHERE player_name=%s AND jersey_number=%s"
        data = (name, jersey)

        cursor.execute(sql, data)
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            return redirect(url_for("fixtures"))
        else:
            message = "Login failed: player not found"
            return render_template("login.html", message=message)


# View all fixtures
@app.route('/fixtures')
def fixtures():
    matches = Match.query.order_by(Match.date.desc()).all()
    return render_template('index.html', matches=matches)


# Add a match
@app.route('/add', methods=['GET', 'POST'])
def add_match():
    if request.method == 'POST':
        match_result = request.form['match_result']
        match_lineup = request.form['match_lineup']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        match_location = request.form['match_location']
        match_time = request.form['match_time']

        new_match = Match(
            match_result=match_result,
            match_lineup=match_lineup,
            date=date,
            match_location=match_location,
            match_time=match_time
        )

        db.session.add(new_match)
        db.session.commit()
        return redirect(url_for('fixtures'))

    return render_template('add_match.html')


# View past fixtures
@app.route('/past')
def past_fixtures():
    today = datetime.today().date()
    past_matches = Match.query.filter(Match.date < today).order_by(Match.date.desc()).all()
    return render_template('past_fixtures.html', matches=past_matches)


# Edit match
@app.route('/edit/<int:match_id>', methods=['GET', 'POST'])
def edit_match(match_id):
    match = Match.query.get_or_404(match_id)

    if request.method == 'POST':
        match.match_result = request.form['match_result']
        match.match_lineup = request.form['match_lineup']
        match.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        match.match_location = request.form['match_location']
        match.match_time = request.form['match_time']

        db.session.commit()
        return redirect(url_for('past_fixtures'))

    return render_template('edit_match.html', match=match)


# Register player (MySQL)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form["name"]
        age = request.form["age"]
        jersey = request.form["jersey"]
        nationality = request.form["nationality"]

        connection = pymysql.connect(host="localhost", user="root", password="", database="ctg_fc")
        cursor = connection.cursor()
        sql = "INSERT INTO player(age, player_name, jersey_number, nationality) values(%s, %s, %s, %s)"
        data = (age, name, jersey, nationality)
        cursor.execute(sql, data)
        connection.commit()
        cursor.close()
        connection.close()


        message = "Registered successfully"
        return render_template("register.html", message=message)




# Match statistics route
@app.route('/stats')
def stats():
    total_matches = Match.query.count()
    past_matches = Match.query.filter(Match.date < datetime.today().date()).count()
    upcoming_matches = Match.query.filter(Match.date >= datetime.today().date()).count()

    # Example: Count matches per location (could show most common stadium)
    location_stats = db.session.query(
        Match.match_location, db.func.count(Match.match_location)
    ).group_by(Match.match_location).all()

    return render_template('stats.html', 
                           total_matches=total_matches, 
                           past_matches=past_matches,
                           upcoming_matches=upcoming_matches,
                           location_stats=location_stats)




@app.route("/add_stats", methods=["GET", "POST"])
def add_stats():
    if request.method == "GET":
        # Fetch all matches to display in dropdown
        connection = pymysql.connect(host="localhost", user="root", password="", database="ctg_fc")
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, match_result FROM matches")  # ✅ FIXED table name
        matches = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template("add_stats.html", matches=matches)

    else:
        # Process form submission
        player_name = request.form["player_name"]
        goals = request.form["goals"]
        assists = request.form["assists"]
        rating = request.form["rating"]
        cardings = request.form["cardings"]
        match_id = request.form["match_id"]

        # Insert into stats table
        connection = pymysql.connect(host="localhost", user="root", password="", database="ctg_fc")
        cursor = connection.cursor()
        sql = """
            INSERT INTO stats (player_name, goals, assists, player_ratings, cardings, match_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        data = (player_name, goals, assists, rating, cardings, match_id)
        cursor.execute(sql, data)
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("view_stats"))









@app.route("/view_stats")
def view_stats():
    connection = pymysql.connect(host="localhost", user="root", password="", database="ctg_fc")
    cursor = connection.cursor(pymysql.cursors.DictCursor)  # Optional: use dicts

    sql = "SELECT id, player_name, goals, assists, player_ratings, cardings FROM stats"
    cursor.execute(sql)
    stats = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("view_stats.html", stats=stats)





@app.route("/match_stats/<int:match_id>")
def match_stats(match_id):
    connection = pymysql.connect(host="localhost", user="root", password="", database="ctg_fc")
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # ✅ FIXED: table name is now matches
    cursor.execute("SELECT * FROM matches WHERE id = %s", (match_id,))
    match = cursor.fetchone()

    # Get stats for that match
    cursor.execute("""
        SELECT player_name, goals, assists, player_ratings, cardings
        FROM stats WHERE match_id = %s
    """, (match_id,))
    stats = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("match_stats.html", match=match, stats=stats)








# Create database tables and run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
