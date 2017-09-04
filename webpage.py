from flask import Flask, request, render_template, redirect
import strength_percentiles as sp
import sqlite3 as sq
app = Flask(__name__)

percentiles_string = ""

@app.before_request
def before_request():
    sp.populate_database(sp.QUOTE_PAGE, sp.DATABASE, sp.MEET_RESULTS_TABLE)

@app.route('/')
def index():
    return render_template("home.html", percentiles_string=percentiles_string)

@app.route('/enter_lifts')
def get_lifts():
    return render_template("enter_lifts.html")

@app.route('/calculate', methods=['POST'])
def calculate_percentiles():
    connection = sq.connect(sp.DATABASE)
    categories = {sp.GENDER: "", sp.EQUIPMENT: "", sp.PROFESSIONAL_STATUS: ""}
    competition = sp.get_population_by_categories(connection,
                                                  sp.MEET_RESULTS_TABLE,
                                                  categories)
    lifts = {sp.SQUAT: None, sp.BENCH: None, sp.DEADLIFT: None, sp.TOTAL: None}
    for lift in (sp.SQUAT, sp.BENCH, sp.DEADLIFT):
        try:
            lifts[lift] = float(request.form[lift])
        except ValueError:
            lifts[lift] = None
    try:
        lifts[sp.TOTAL] = sum(lifts.values())
    except TypeError:
        lifts[sp.TOTAL] = None
    percentiles = sp.find_percentile(competition, lifts)
    global percentiles_string
    percentiles_string = sp.format_percentiles(percentiles)
    connection.close()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
