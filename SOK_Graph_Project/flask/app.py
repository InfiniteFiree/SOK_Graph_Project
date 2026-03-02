import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from block_visualizer.block_visualizer import BlockVisualizer
from flask import Flask, render_template, url_for

app = Flask(__name__)
app.config['APP_NAME'] = "Graph Visualizer"

@app.route("/")
def index():

    # PRIVREMENI TEST GRAPH (kasnije dolazi iz platforme)
    graph = {
        "nodes": [
            {"id": "1", "name": "John", "age": 53},
            {"id": "2", "name": "Mike", "age": 25},
            {"id": "3", "name": "Lucy", "age": 15},
        ],
        "edges": [
            {"source": "1", "target": "2"},
            {"source": "1", "target": "3"},
        ]
    }

    visualizer = BlockVisualizer()
    graph_html = visualizer.visualize(graph)

    return render_template(
        "index.html",
        title=app.config['APP_NAME'],
        graph_html=graph_html
    )

if __name__ == "__main__":
    app.run(debug=True)