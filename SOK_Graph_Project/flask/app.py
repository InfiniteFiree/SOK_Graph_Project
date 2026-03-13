import sys
import os
import logging

from jinja2 import ChoiceLoader, FileSystemLoader
from flask import Flask, render_template, request, redirect, url_for

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

from core.service.use_cases.workspace import Workspace
from core.service.use_cases.workspace_manager import WorkspaceManager
from core.service.use_cases.tree_view import TreeView
from core.service.use_cases.bird_view import BirdView
from core.service.use_cases.plugin_recognition import PluginService

plugin_service = PluginService()


app = Flask(__name__)
app.config['APP_NAME'] = "Graph Visualizer"
app.logger.setLevel(logging.INFO)

plugins = plugin_service.load_plugins()
workspace_manager = WorkspaceManager()

# Allow Flask to load templates both from flask/templates and core/templates
flask_templates = os.path.join(project_root, 'flask', 'templates')
core_templates = os.path.join(project_root, 'core', 'templates')

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(flask_templates),
    FileSystemLoader(core_templates)
])


@app.route("/workspace/create")
def create_workspace():
    selected_data_source = request.args.get("data_source", "csv")
    selected_visualizer = request.args.get("type", "simple_visualizer")
    source_path = request.args.get("source_path", "")

    if not source_path:
        return redirect(url_for("index"))

    try:
        graph = plugin_service.load_graph_from_selected_source(
            plugins=plugins,
            selected_data_source=selected_data_source,
            source_path=source_path,
            project_root=project_root
        )
    except ValueError as e:
        active_workspace = workspace_manager.get_active()
        load_targets = plugin_service.list_plugin_load_targets(project_root)

        return render_template(
            "index.html",
            title=app.config['APP_NAME'],
            graph_html="",
            bird_view_html="",
            tree_view_html="",
            plugins=plugins["visualization"],
            data_plugins=plugins["data_source"],
            selected_visualizer=selected_visualizer,
            selected_data_source=selected_data_source,
            selected_source_path=source_path,
            load_targets=load_targets,
            workspaces=workspace_manager.list_workspaces(),
            active_workspace_id=active_workspace.id if active_workspace else None,
            workspace_error=str(e),
        )

    workspace = Workspace(
        graph=graph,
        name=os.path.basename(source_path.rstrip("/\\")) or source_path,
        visualizer_type=selected_visualizer,
        data_source=selected_data_source,
        source_path=source_path
    )

    workspace_manager.add_workspace(workspace)
    workspace_manager.set_active(workspace.id)

    return redirect(url_for("index", workspace_id=workspace.id))


@app.route("/workspace/delete")
def delete_workspace():
    workspace_id = request.args.get("workspace_id")

    if workspace_id:
        workspace_manager.remove_workspace(workspace_id)

    active_workspace = workspace_manager.get_active()
    if active_workspace:
        return redirect(url_for("index", workspace_id=active_workspace.id))

    return redirect(url_for("index"))


@app.route("/")
def index():
    workspace_id = request.args.get("workspace_id")
    if workspace_id:
        workspace_manager.set_active(workspace_id)

    active_workspace = workspace_manager.get_active()

    load_targets = plugin_service.list_plugin_load_targets(project_root)

    # If no workspace exists yet, auto-create one from the first available target
    if active_workspace is None:
        selected_data_source = request.args.get("data_source", "csv")
        selected_visualizer = request.args.get("type", "simple_visualizer")

        if not load_targets:
            return "No loadable files/folders found under plugins/"

        source_path = request.args.get("source_path", load_targets[0]["value"])

        graph = plugin_service.load_graph_from_selected_source(
            plugins=plugins,
            selected_data_source=selected_data_source,
            source_path=source_path,
            project_root=project_root
        )

        active_workspace = Workspace(
            graph=graph,
            name=os.path.basename(source_path.rstrip("/\\")) or source_path,
            visualizer_type=selected_visualizer,
            data_source=selected_data_source,
            source_path=source_path
        )

        workspace_manager.add_workspace(active_workspace)
        workspace_manager.set_active(active_workspace.id)

    graph = active_workspace.graph
    app.config["GRAPH"] = graph

    selected_visualizer = active_workspace.visualizer_type
    selected_data_source = active_workspace.data_source
    selected_source_path = active_workspace.source_path

    visualizer = plugins["visualization"].get(selected_visualizer)

    if visualizer is None:
        if plugins["visualization"]:
            visualizer = next(iter(plugins["visualization"].values()))
            selected_visualizer = visualizer.identifier()
            print(f"[app] Plugin '{active_workspace.visualizer_type}' nije pronađen, koristim prvi dostupan: '{selected_visualizer}'")
        else:
            return "No visualization plugins loaded"

    graph_html = visualizer.visualize(graph, workspace_id=active_workspace.id)

    bird_view = BirdView()
    bird_view_html = bird_view.render(workspace_id=active_workspace.id)

    tree_view = TreeView(graph)
    tree_view_html = tree_view.render(workspace_id=active_workspace.id)

    return render_template(
        "index.html",
        title=app.config['APP_NAME'],
        graph_html=graph_html,
        bird_view_html=bird_view_html,
        tree_view_html=tree_view_html,
        plugins=plugins["visualization"],
        data_plugins=plugins["data_source"],
        selected_visualizer=selected_visualizer,
        selected_data_source=selected_data_source,
        selected_source_path=selected_source_path,
        load_targets=load_targets,
        workspaces=workspace_manager.list_workspaces(),
        active_workspace_id=active_workspace.id,
        workspace_error=None,
    )


if __name__ == "__main__":
    app.run(debug=True)