from flask import Flask, render_template, url_for

app = Flask(__name__)
app.config['APP_NAME'] = "Graph Visualizer"

@app.route("/")
def index():
    return render_template('index.html', title=app.config['APP_NAME'])

if __name__ == "__main__":
    app.run(debug=True)