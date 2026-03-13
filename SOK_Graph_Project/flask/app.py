import sys
import os
# import importlib.util
import logging
# import json

from jinja2 import ChoiceLoader, FileSystemLoader
from flask import Flask, render_template, request, jsonify

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

from core.service.use_cases.tree_view import TreeView
from core.service.use_cases.bird_view import BirdView
from core.service.use_cases.graph_search_filter import GraphSearchFilter
from plugins.csv_data_source.csv_db.csv_db import CsvDb
#from plugins.plugin_loader import load_plugins
from core.service.use_cases.plugin_recognition import PluginService

plugin_service = PluginService()
graph_search_filter = GraphSearchFilter()

def get_plugins():
    return plugin_service.load_plugins()

app = Flask(__name__)
app.config['APP_NAME'] = "Graph Visualizer"
app.logger.setLevel(logging.INFO)
plugins = get_plugins()


def build_csv_db(mode, dataset):
    base_dir = os.path.abspath(
        os.path.join(project_root, 'plugins', 'csv_data_source', 'csv_data')
    )

    if mode == "single_file":
        csv_path = os.path.join(base_dir, "csv.csv")
        return CsvDb(mode="single_file", csv_path=csv_path)

    nodes_path = os.path.join(base_dir, "nodes.csv")
    edges_path = os.path.join(
        base_dir,
        "edges_cyclic.csv" if dataset == "cyclic" else "edges.csv"
    )

    return CsvDb(
        mode="separate_files",
        nodes_path=nodes_path,
        edges_path=edges_path
    )


def load_graph(mode, dataset, selected_data_source):
    csv_db = build_csv_db(mode, dataset)

    if selected_data_source:
        ds_plugin = plugins["data_source"].get(selected_data_source)
        if ds_plugin:
            return ds_plugin.load()

    return csv_db.load()


def resolve_visualizer(selected_visualizer):
    visualizer = plugins["visualization"].get(selected_visualizer)

    if visualizer is not None:
        return visualizer

    if not plugins["visualization"]:
        return None

    fallback = next(iter(plugins["visualization"].values()))
    print(
        f"[app] Plugin '{selected_visualizer}' nije pronađen, "
        f"koristim prvi dostupan: '{fallback.identifier()}'"
    )
    return fallback

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
    selected_data_source = request.args.get("data_source", "csv")
    selected_visualizer = request.args.get("type", "simple_visualizer")

    graph = load_graph(mode, dataset, selected_data_source)
    graph_search_filter.set_source_graph(graph)
    app.config["GRAPH"] = graph_search_filter.filtered_graph

    visualizer = resolve_visualizer(selected_visualizer)
    if visualizer is None:
        return "No visualization plugins loaded"

    graph_html = visualizer.visualize(graph_search_filter.filtered_graph)

    # Bird view
    bird_view = BirdView()
    bird_view_html = bird_view.render()

    # Tree view
    tree_view = TreeView(graph_search_filter.filtered_graph)
    tree_view_html = tree_view.render()

    return render_template(
        "index.html",
        title=app.config['APP_NAME'],
        graph_html=graph_html,
        bird_view=bird_view_html,
        tree_view_html=tree_view_html,
        selected_mode=mode,
        selected_dataset=dataset,
        plugins=plugins["visualization"],
        data_plugins=plugins["data_source"],
        selected_visualizer=selected_visualizer,
        selected_data_source=selected_data_source,
    )


@app.route("/apply_filter", methods=["POST"])
def apply_filter():
    payload = request.get_json(silent=True) or {}

    attribute = payload.get("attribute", "")
    operator = payload.get("operator", "=")
    value = payload.get("value", "")
    selected_visualizer = payload.get("type", "simple_visualizer")

    filtered_graph = graph_search_filter.filter(attribute, operator, value)

    visualizer = resolve_visualizer(selected_visualizer)
    if visualizer is None:
        return jsonify({"error": "No visualization plugins loaded"}), 400

    app.config["GRAPH"] = filtered_graph
    graph_html = visualizer.visualize(filtered_graph)
    return jsonify({"graph_html": graph_html})


@app.route("/clear_filters", methods=["POST"])
def clear_filters():
    payload = request.get_json(silent=True) or {}

    mode = payload.get("mode", "separate_files")
    dataset = payload.get("dataset", "acyclic")
    selected_data_source = payload.get("data_source", "csv")
    selected_visualizer = payload.get("type", "simple_visualizer")

    source_graph = load_graph(mode, dataset, selected_data_source)
    filtered_graph = graph_search_filter.clear_filters(source_graph)

    visualizer = resolve_visualizer(selected_visualizer)
    if visualizer is None:
        return jsonify({"error": "No visualization plugins loaded"}), 400

    app.config["GRAPH"] = filtered_graph
    graph_html = visualizer.visualize(filtered_graph)
    return jsonify({"graph_html": graph_html})


@app.route("/search", methods=["POST"])
def search_graph():
    payload = request.get_json(silent=True) or {}

    query = payload.get("query", "")
    selected_visualizer = payload.get("type", "simple_visualizer")

    result_graph = graph_search_filter.search(query)

    visualizer = resolve_visualizer(selected_visualizer)
    if visualizer is None:
        return jsonify({"error": "No visualization plugins loaded"}), 400

    graph_html = visualizer.visualize(result_graph)
    return jsonify({"graph_html": graph_html})

if __name__ == "__main__":
    app.run(debug=True)