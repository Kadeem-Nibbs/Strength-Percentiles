from flask import Flask, request, render_template, redirect
import strength_percentiles as sp

app = Flask(__name__)
percentiles = ""

@app.before_request
def before_request():
    sp.populate_database(sp.QUOTE_PAGE, sp.DATABASE, sp.MEET_RESULTS_TABLE)

@app.route('/')
def index():
    return render_template("home.html", percentiles=percentiles)

# Never getting called, can't do anything with lifts
@app.route('/enter_lifts')
def get_lifts():
    return render_template("enter_lifts.html")

@app.route('/calculate', methods=['POST'])
def calculate_percentiles():
    connection = sp.sq.connect(sp.DATABASE)
    categories = {sp.GENDER: "", sp.EQUIPMENT: "", sp.PROFESSIONAL_STATUS: ""}
    competition = sp.get_population_by_categories(connection,
                                                  sp.MEET_RESULTS_TABLE,
                                                  categories)
    squat = float(request.form['squat'])
    bench = float(request.form['bench'])
    deadlift = float(request.form['deadlift'])
    total = squat + bench + deadlift
    lifts = {sp.SQUAT: squat,
             sp.BENCH: bench,
             sp.DEADLIFT: bench,
             sp.TOTAL: total}
    global percentiles
    percentiles = str(sp.find_percentile(competition, lifts))
    connection.close()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
