import sys
import os
import importlib.util
import logging
import json

from jinja2 import ChoiceLoader, FileSystemLoader
from flask import Flask, render_template, request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

from json_data_source.json_db.json_db import JSONRepository
from core.service.use_cases.plugin_recognition import recognize_plugin
from core.service.use_cases.tree_view import TreeView
from core.service.use_cases.bird_view import BirdView
from flask import Flask, render_template, request
from csv_data_source.csv_db.csv_db import CsvDb


app = Flask(__name__)
app.config['APP_NAME'] = "Graph Visualizer"
app.logger.setLevel(logging.INFO)

# Allow Flask to load templates both from flask/templates and core/templates
flask_templates = os.path.join(project_root, 'flask', 'templates')
core_templates = os.path.join(project_root, 'core', 'templates')

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(flask_templates),
    FileSystemLoader(core_templates)
])


@app.route("/")
def index():
    mode = request.args.get("mode", "separate_files")
    dataset = request.args.get("dataset", "acyclic")
    user_choice = request.args.get("type", "simple")  # "simple" or "block"

    base_dir = os.path.abspath(
        os.path.join(project_root, 'csv_data_source', 'csv_data')
    )

    if mode == "single_file":
        csv_path = os.path.join(base_dir, "csv.csv")
        csv_db = CsvDb(
            mode="single_file",
            csv_path=csv_path
        )
    else:
        nodes_path = os.path.join(base_dir, "nodes.csv")
        edges_path = os.path.join(
            base_dir,
            "edges_cyclic.csv" if dataset == "cyclic" else "edges.csv"
        )

        csv_db = CsvDb(
            mode="separate_files",
            nodes_path=nodes_path,
            edges_path=edges_path
        )

    # Load graph from CSV
    graph = csv_db.load()

    # Load graph from JSON
    repository = JSONRepository("test_graph.json")
    json_graph = repository.read_from_file()
    json_graph_dict = repository.graph_to_dict(json_graph)

    # if json_graph_dict is None:
    #     app.logger.info("Failed to load graph from file.")
    # else:
    #     app.logger.info("Graph structure:\n%s", json.dumps(json_graph_dict, indent=2, ensure_ascii=False))

    # Main visualization
    app.config["GRAPH"] = graph
    user_choice = request.args.get("type")  # simple ili block
    visualizer = recognize_plugin(user_choice)
    graph_html = visualizer.visualize(graph)

    # Bird view
    bird_view = BirdView()
    bird_view_html = bird_view.render()

    # Tree view
    tree_view = TreeView(graph)
    tree_view_html = tree_view.render()

    return render_template(
        "index.html",
        title=app.config['APP_NAME'],
        graph_html=graph_html,
        bird_view=bird_view_html,
        tree_view_html=tree_view_html,
        selected_visualizer=user_choice,
        selected_mode=mode,
        selected_dataset=dataset
    )


if __name__ == "__main__":
    app.run(debug=True)