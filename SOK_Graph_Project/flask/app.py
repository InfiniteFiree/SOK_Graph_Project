import sys
import os
import logging
import subprocess

from jinja2 import ChoiceLoader, FileSystemLoader
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

from core.build.lib.service.use_cases.workspace import Workspace
from core.build.lib.service.use_cases.workspace_manager import WorkspaceManager
from core.build.lib.service.use_cases.tree_view import TreeView
from core.build.lib.service.use_cases.bird_view import BirdView
from core.build.lib.service.use_cases.plugin_recognition import PluginService

app = Flask(__name__)
app.config["APP_NAME"] = "Graph Visualizer"
app.logger.setLevel(logging.INFO)

plugin_service = PluginService()
plugin_service.refresh_plugins()

workspace_manager = WorkspaceManager()

# Allow Flask to load templates both from flask/templates and core/templates
flask_templates = os.path.join(project_root, "flask", "templates")
core_templates = os.path.join(project_root, "core", "templates")

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(flask_templates),
    FileSystemLoader(core_templates)
])


def get_active_plugins():
    return plugin_service.get_active_plugins()


def get_plugin_summary():
    return plugin_service.get_plugin_summary()


def build_visualization_model(visualizer, graph, workspace_id):
    """
    Visualization plugins return a dict model, not HTML.
    """
    return visualizer.visualize(graph, workspace_id=workspace_id)


def render_index(
    active_workspace=None,
    selected_visualizer="simple_visualizer",
    selected_data_source="csv",
    selected_source_path="",
    workspace_error=None,
):
    active_plugins = get_active_plugins()
    plugin_summary = get_plugin_summary()
    load_targets = plugin_service.list_plugin_load_targets(project_root)

    if active_workspace is None:
        return render_template(
            "index.html",
            title=app.config["APP_NAME"],
            graph_html="",
            visualization_model=None,
            bird_view_html="",
            tree_view_html="",
            plugins=active_plugins["visualization"],
            data_plugins=active_plugins["data_source"],
            plugin_summary=plugin_summary,
            selected_visualizer=selected_visualizer,
            selected_data_source=selected_data_source,
            selected_source_path=selected_source_path,
            load_targets=load_targets,
            workspaces=workspace_manager.list_workspaces(),
            active_workspace_id=None,
            workspace_error=workspace_error,
            no_workspace=True,
        )

    graph = active_workspace.graph
    graph_search_filter.set_source_graph(graph)
    app.config["GRAPH"] = graph_search_filter.filtered_graph

    selected_visualizer = active_workspace.visualizer_type
    selected_data_source = active_workspace.data_source
    selected_source_path = active_workspace.source_path

    visualizer = active_plugins["visualization"].get(selected_visualizer)

    if visualizer is None:
        if active_plugins["visualization"]:
            visualizer = next(iter(active_plugins["visualization"].values()))
            selected_visualizer = visualizer.identifier()
            app.logger.warning(
                "Plugin '%s' was not found, using first available plugin '%s'",
                active_workspace.visualizer_type,
                selected_visualizer,
            )
        else:
            return render_template(
                "index.html",
                title=app.config["APP_NAME"],
                graph_html="",
                visualization_model=None,
                bird_view_html="",
                tree_view_html="",
                plugins={},
                data_plugins=active_plugins["data_source"],
                plugin_summary=plugin_summary,
                selected_visualizer=selected_visualizer,
                selected_data_source=selected_data_source,
                selected_source_path=selected_source_path,
                load_targets=load_targets,
                workspaces=workspace_manager.list_workspaces(),
                active_workspace_id=active_workspace.id,
                workspace_error="No visualization plugins are available.",
                no_workspace=False,
            )

    visualization_model = build_visualization_model(
        visualizer,
        graph_search_filter.filtered_graph,
        active_workspace.id
    )

    bird_view = BirdView()
    bird_view_html = bird_view.render(workspace_id=active_workspace.id)

    tree_view = TreeView(graph_search_filter.filtered_graph)
    tree_view_html = tree_view.render(workspace_id=active_workspace.id)

    return render_template(
        "index.html",
        title=app.config["APP_NAME"],
        graph_html="",
        visualization_model=visualization_model,
        bird_view_html=bird_view_html,
        tree_view_html=tree_view_html,
        plugins=active_plugins["visualization"],
        data_plugins=active_plugins["data_source"],
        plugin_summary=plugin_summary,
        selected_visualizer=selected_visualizer,
        selected_data_source=selected_data_source,
        selected_source_path=selected_source_path,
        load_targets=load_targets,
        workspaces=workspace_manager.list_workspaces(),
        active_workspace_id=active_workspace.id,
        workspace_error=workspace_error,
        no_workspace=False,
    )


@app.route("/plugins")
def list_plugins():
    return jsonify(plugin_service.get_plugin_summary())


@app.route("/plugins/refresh", methods=["POST"])
def refresh_plugins():
    plugin_service.refresh_plugins()
    return redirect(url_for("index"))


@app.route("/plugins/install", methods=["POST"])
def install_plugin():
    plugin_path = request.form.get("plugin_path", "").strip()
    editable = request.form.get("editable", "true").lower() == "true"

    if not plugin_path:
        return render_index(
            active_workspace=workspace_manager.get_active(),
            workspace_error="Plugin path is required."
        )

    abs_plugin_path = os.path.abspath(os.path.join(project_root, plugin_path))

    if not os.path.exists(abs_plugin_path):
        return render_index(
            active_workspace=workspace_manager.get_active(),
            workspace_error=f"Plugin path does not exist: {plugin_path}"
        )

    cmd = [sys.executable, "-m", "pip", "install"]
    if editable:
        cmd.append("-e")
    cmd.append(abs_plugin_path)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        error_output = (result.stderr or result.stdout or "Unknown pip install error").strip()
        return render_index(
            active_workspace=workspace_manager.get_active(),
            workspace_error=f"Plugin install failed: {error_output}"
        )

    plugin_service.refresh_plugins()
    return redirect(url_for("index"))


@app.route("/plugins/uninstall", methods=["POST"])
def uninstall_plugin():
    distribution = request.form.get("distribution", "").strip()

    if not distribution:
        return render_index(
            active_workspace=workspace_manager.get_active(),
            workspace_error="Plugin distribution name is required."
        )

    cmd = [sys.executable, "-m", "pip", "uninstall", "-y", distribution]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        error_output = (result.stderr or result.stdout or "Unknown pip uninstall error").strip()
        return render_index(
            active_workspace=workspace_manager.get_active(),
            workspace_error=f"Plugin uninstall failed: {error_output}"
        )

    plugin_service.refresh_plugins()
    return redirect(url_for("index"))


@app.route("/core-assets/main_view/<path:filename>")
def core_main_view_assets(filename):
    assets_dir = os.path.join(project_root, "core", "assets", "main_view")
    return send_from_directory(assets_dir, filename)


def resolve_visualizer(selected_visualizer):
    visualizer = plugins["visualization"].get(selected_visualizer)

    if visualizer is None:
        if plugins["visualization"]:
            visualizer = next(iter(plugins["visualization"].values()))
            selected_visualizer = visualizer.identifier()
        else:
            return None, selected_visualizer

    return visualizer, selected_visualizer


@app.route("/workspace/create")
def create_workspace():
    selected_data_source = request.args.get("data_source", "csv")
    selected_visualizer = request.args.get("type", "simple_visualizer")
    source_path = request.args.get("source_path", "")

    if not source_path:
        return redirect(url_for("index"))

    try:
        graph = plugin_service.load_graph_from_selected_source(
            selected_data_source=selected_data_source,
            source_path=source_path,
            project_root=project_root
        )
    except ValueError as e:
        active_workspace = workspace_manager.get_active()
        return render_index(
            active_workspace=active_workspace,
            selected_visualizer=selected_visualizer,
            selected_data_source=selected_data_source,
            selected_source_path=source_path,
            load_targets=load_targets,
            workspaces=workspace_manager.list_workspaces(),
            active_workspace_id=active_workspace.id if active_workspace else None,
            cli_history=active_workspace.cli.command_history if active_workspace else [],
            cli_feedback=None,
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
    selected_data_source = request.args.get("data_source", "csv")
    selected_visualizer = request.args.get("type", "simple_visualizer")
    selected_source_path = request.args.get("source_path", "")

    workspace_id = request.args.get("workspace_id")
    if workspace_id:
        workspace_manager.set_active(workspace_id)

    active_workspace = workspace_manager.get_active()

    return render_index(
        active_workspace=active_workspace,
        selected_visualizer=selected_visualizer,
        selected_data_source=selected_data_source,
        selected_source_path=selected_source_path,
        workspace_error=None,
    )


@app.route("/cli/execute", methods=["POST"])
def execute_cli_command():
    payload = request.get_json(silent=True) or {}
    workspace_id = payload.get("workspace_id")
    workspace = workspace_manager.get_workspace(workspace_id) if workspace_id else workspace_manager.get_active()

    if workspace is None:
        return jsonify({"error": "No active workspace"}), 400

    selected_visualizer = payload.get("type", workspace.visualizer_type)
    visualizer, selected_visualizer = resolve_visualizer(selected_visualizer)
    if visualizer is None:
        return jsonify({"error": "No visualization plugins loaded"}), 400

    command = payload.get("command", "")

    try:
        result = workspace.cli.execute(command)
        graph_for_view = result.get("display_graph", workspace.search_filter.filtered_graph)
        message = result.get("message", "Command executed")
    except ValueError as e:
        graph_for_view = workspace.search_filter.filtered_graph
        message = str(e)
        response_code = 400
    else:
        response_code = 200

    graph_html = visualizer.visualize(graph_for_view, workspace_id=workspace.id)
    tree_view_html = TreeView(graph_for_view).render(workspace_id=workspace.id)
    bird_view_html = BirdView().render(workspace_id=workspace.id)

    return jsonify({
        "graph_html": graph_html,
        "tree_view_html": tree_view_html,
        "bird_view_html": bird_view_html,
        "cli_history": workspace.cli.command_history,
        "cli_feedback": message,
        "selected_visualizer": selected_visualizer,
    }), response_code


@app.route("/apply_filter", methods=["POST"])
def apply_filter():
    payload = request.get_json(silent=True) or {}
    workspace_id = payload.get("workspace_id")
    workspace = workspace_manager.get_workspace(workspace_id) if workspace_id else workspace_manager.get_active()

    if workspace is None:
        return jsonify({"error": "No active workspace"}), 400

    workspace_id = payload.get("workspace_id")
    if workspace_id:
        workspace_manager.set_active(workspace_id)

    active_workspace = workspace_manager.get_active()
    if active_workspace is None:
        return jsonify({"error": "No active workspace"}), 400

    attribute = payload.get("attribute", "")
    operator = payload.get("operator", "=")
    value = payload.get("value", "")
    selected_visualizer = payload.get("type", active_workspace.visualizer_type)

    graph_search_filter.set_source_graph(active_workspace.graph)
    filtered_graph = workspace.search_filter.filter(attribute, operator, value)

    try:
        visualizer = plugin_service.get_plugin("visualization", selected_visualizer, active_only=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    app.config["GRAPH"] = filtered_graph
    visualization_model = build_visualization_model(
        visualizer,
        filtered_graph,
        active_workspace.id
    )

    return jsonify({
        "graph_html": "",
        "visualization_model": visualization_model
    })


@app.route("/clear_filters", methods=["POST"])
def clear_filters():
    payload = request.get_json(silent=True) or {}
    workspace_id = payload.get("workspace_id")
    workspace = workspace_manager.get_workspace(workspace_id) if workspace_id else workspace_manager.get_active()

    workspace_id = payload.get("workspace_id")
    if workspace_id:
        workspace_manager.set_active(workspace_id)

    active_workspace = workspace_manager.get_active()
    if active_workspace is None:
        return jsonify({"error": "No active workspace"}), 400

    selected_visualizer = payload.get("type", active_workspace.visualizer_type)

    fresh_graph = plugin_service.load_graph_from_selected_source(
        plugins=plugins,
        selected_data_source=workspace.data_source,
        source_path=workspace.source_path,
        project_root=project_root
    )
    workspace.graph = fresh_graph
    filtered_graph = workspace.search_filter.clear_filters(fresh_graph)

    try:
        visualizer = plugin_service.get_plugin("visualization", selected_visualizer, active_only=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    app.config["GRAPH"] = filtered_graph
    visualization_model = build_visualization_model(
        visualizer,
        filtered_graph,
        active_workspace.id
    )

    return jsonify({
        "graph_html": "",
        "visualization_model": visualization_model
    })


@app.route("/search", methods=["POST"])
def search_graph():
    payload = request.get_json(silent=True) or {}
    workspace_id = payload.get("workspace_id")
    workspace = workspace_manager.get_workspace(workspace_id) if workspace_id else workspace_manager.get_active()

    if workspace is None:
        return jsonify({"error": "No active workspace"}), 400

    workspace_id = payload.get("workspace_id")
    if workspace_id:
        workspace_manager.set_active(workspace_id)

    active_workspace = workspace_manager.get_active()
    if active_workspace is None:
        return jsonify({"error": "No active workspace"}), 400

    query = payload.get("query", "")
    selected_visualizer = payload.get("type", active_workspace.visualizer_type)

    result_graph = workspace.search_filter.search(query)

    try:
        visualizer = plugin_service.get_plugin("visualization", selected_visualizer, active_only=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    visualization_model = build_visualization_model(
        visualizer,
        result_graph,
        active_workspace.id
    )

    return jsonify({
        "graph_html": "",
        "visualization_model": visualization_model
    })


if __name__ == "__main__":
    app.run(debug=True)