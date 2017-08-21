from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("enter_lifts.html")

# Never getting called, can't do anything with lifts
@app.route('/', methods=['POST'])
def retrieve_input():
    print "Called retrieve"
    lifts = {}
    lifts['squat'] = request.form['squat']
    lifts['bench'] = request.form['bench']
    lifts['deadlift'] = request.form['deadlift']
    return lifts

if __name__ == "__main__":
    app.run(debug=True)
