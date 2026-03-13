from typing import List
import os
import sys
import importlib

from api.graph.api.services.plugin import Plugin, DataSourcePlugin, VisualizationPlugin

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

PLUGIN_FOLDER = os.path.join(PROJECT_ROOT, "plugins")
PARENT_FOLDER = PROJECT_ROOT

# Dodaj root u sys.path ako već nije
if PARENT_FOLDER not in sys.path:
    sys.path.insert(0, PARENT_FOLDER)


class PluginService(object):

    def __init__(self):
        self.plugins = {
            "visualization": {},
            "data_source": {}
        }

    def load_plugins(self):

        # očisti prethodne plugine (korisno kod Flask debug reload)
        self.plugins["visualization"].clear()
        self.plugins["data_source"].clear()

        # Prođi kroz sve .py fajlove u PLUGIN_FOLDER i podfolderima
        for root, _, files in os.walk(PLUGIN_FOLDER):
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py"]:
                    rel_path = os.path.relpath(os.path.join(root, file), PARENT_FOLDER)
                    module_name = rel_path[:-3].replace(os.sep, ".")

                    try:
                        if module_name in sys.modules:
                            module = importlib.reload(sys.modules[module_name])
                        else:
                            module = importlib.import_module(module_name)
                    except Exception as e:
                        print(f"[plugin_recognition] Warning: Failed to import {module_name}: {e}")
                        continue

                    # traži sve klase koje nasledjuju Plugin
                    for attr in dir(module):
                        obj = getattr(module, attr)

                        if isinstance(obj, type) and issubclass(obj, Plugin) and obj != Plugin:
                            try:
                                instance = obj()
                            except TypeError:
                                continue

                            if isinstance(instance, VisualizationPlugin):
                                self.plugins["visualization"][instance.identifier()] = instance

                            elif isinstance(instance, DataSourcePlugin):
                                self.plugins["data_source"][instance.identifier()] = instance

        return self.plugins
    
    def list_plugin_load_targets(self, project_root: str):
        """
        Returns loadable files/folders under plugins/.
        Paths are relative to project_root.
        """
        plugins_root = os.path.join(project_root, "plugins")
        results = []

        if not os.path.isdir(plugins_root):
            return results

        for root, dirs, files in os.walk(plugins_root):
            rel_root = os.path.relpath(root, project_root).replace("\\", "/")

            # CSV folder target
            if "nodes.csv" in files and "edges.csv" in files:
                results.append({
                    "value": rel_root,
                    "label": f"{rel_root}/  [CSV folder]"
                })

            # Single-file targets
            for filename in files:
                lower = filename.lower()
                if (lower.endswith(".csv") or lower.endswith(".json")) and filename not in ["nodes.csv", "edges.csv", "dir.json"]:
                    rel_path = os.path.join(rel_root, filename).replace("\\", "/")
                    results.append({
                        "value": rel_path,
                        "label": rel_path
                    })

        results.sort(key=lambda x: x["label"].lower())
        return results
    
    def detect_source_kind(self, project_root, source_path):
        """
        Detects whether the selected source path is:
        - csv_file
        - csv_folder
        - json_file
        - unknown
        """
        if not source_path:
            return "unknown"

        abs_source_path = os.path.abspath(os.path.join(project_root, source_path))

        if os.path.isfile(abs_source_path):
            lower = abs_source_path.lower()
            if lower.endswith(".csv"):
                return "csv_file"
            if lower.endswith(".json"):
                return "json_file"
            return "unknown"

        if os.path.isdir(abs_source_path):
            entries = set(os.listdir(abs_source_path))
            if "nodes.csv" in entries and "edges.csv" in entries:
                return "csv_folder"
            return "unknown"

        return "unknown"


    def validate_data_source_choice(self, selected_data_source, source_kind):
        """
        Raises ValueError if the chosen plugin clearly does not match the source kind.
        """
        if source_kind in ("csv_file", "csv_folder") and selected_data_source != "csv":
            raise ValueError(
                "The selected source is a CSV file/folder, so you must use the CSV data source plugin."
            )

        if source_kind == "json_file" and selected_data_source != "json":
            raise ValueError(
                "The selected source is a JSON file, so you must use the JSON data source plugin."
            )
        
    def load_graph_from_selected_source(self, plugins, selected_data_source, source_path, project_root):
        source_kind = self.detect_source_kind(project_root, source_path)
        self.validate_data_source_choice(selected_data_source, source_kind)

        abs_source_path = os.path.abspath(os.path.join(project_root, source_path))

        ds_plugin = plugins["data_source"].get(selected_data_source)
        if ds_plugin:
            try:
                return ds_plugin.load(source_path=abs_source_path)
            except TypeError:
                return ds_plugin.load(abs_source_path)

        raise ValueError(f"Unknown data source plugin: {selected_data_source}")