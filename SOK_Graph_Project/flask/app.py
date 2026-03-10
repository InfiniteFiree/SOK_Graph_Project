import sys
import os
import importlib.util

from jinja2 import ChoiceLoader, FileSystemLoader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

tree_view_path = os.path.join(project_root, 'platform', 'service', 'use_cases', 'tree_view.py')
bird_view_path = os.path.join(project_root, 'platform', 'service', 'use_cases', 'bird_view.py')

bird_spec = importlib.util.spec_from_file_location("custom_bird_view", bird_view_path)
bird_module = importlib.util.module_from_spec(bird_spec)
bird_spec.loader.exec_module(bird_module)
BirdView = bird_module.BirdView

tree_spec = importlib.util.spec_from_file_location("custom_tree_view", tree_view_path)
tree_module = importlib.util.module_from_spec(tree_spec)
tree_spec.loader.exec_module(tree_module)
TreeView = tree_module.TreeView

from block_visualizer.block_visualizer import BlockVisualizer
from flask import Flask, render_template, request
from csv_data_source.csv_db.csv_db import CsvDb

app = Flask(__name__)
app.config['APP_NAME'] = "Graph Visualizer"

# Allow Flask to load templates both from flask/templates and platform/templates
flask_templates = os.path.join(project_root, 'flask', 'templates')
core_templates = os.path.join(project_root, 'platform', 'templates')

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(flask_templates),
    FileSystemLoader(core_templates)
])


@app.route("/")
def index():
    mode = request.args.get("mode", "separate_files")
    dataset = request.args.get("dataset", "acyclic")

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

        if dataset == "cyclic":
            edges_path = os.path.join(base_dir, "edges_cyclic.csv")
        else:
            edges_path = os.path.join(base_dir, "edges.csv")

        csv_db = CsvDb(
            mode="separate_files",
            nodes_path=nodes_path,
            edges_path=edges_path
        )

    # Load graph from CSV
    graph_obj = csv_db.load()
    graph = csv_db.to_dict(graph_obj)

    # Main visualization
    visualizer = BlockVisualizer()
    graph_html = visualizer.visualize(graph)

    # Bird view
    bird_view = BirdView()
    bird_view_html = bird_view.render(graph)

    # Tree view placeholder for now.
    # Later, replace html_content or html_path with output from Simple Visualizer.
    tree_view = TreeView(
        html_content=None,
        html_path=None
    )
    tree_view_html = tree_view.render()

    return render_template(
        "index.html",
        title=app.config['APP_NAME'],
        graph_html=graph_html,
        bird_view=bird_view_html,
        tree_view_html=tree_view_html
    )


if __name__ == "__main__":
    app.run(debug=True)