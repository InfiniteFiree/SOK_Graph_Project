from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Dict, Optional
import os

from api.build.lib.graph.api.services.plugin import (
    Plugin,
    DataSourcePlugin,
    VisualizationPlugin,
)


DATA_SOURCE_GROUP = "sok_graph.data_sources"
VISUALIZATION_GROUP = "sok_graph.visualizers"


@dataclass
class PluginRecord:
    identifier: str
    name: str
    category: str
    instance: Plugin
    entry_point_value: str
    distribution: Optional[str]
    active: bool = True


class PluginService:
    def __init__(self):
        self.plugins: Dict[str, Dict[str, PluginRecord]] = {
            "visualization": {},
            "data_source": {},
        }

    # --------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------

    def refresh_plugins(self):
        """
        Rebuild plugin registry from installed entry points.
        Keeps activation state for already-known plugins when possible.
        """
        previous_states = self._snapshot_activation_states()

        self.plugins["visualization"].clear()
        self.plugins["data_source"].clear()

        self._load_entry_point_group(VISUALIZATION_GROUP, "visualization", previous_states)
        self._load_entry_point_group(DATA_SOURCE_GROUP, "data_source", previous_states)

        return self.get_plugins()

    def _load_entry_point_group(self, group_name: str, category: str, previous_states: Dict[str, bool]):
        try:
            eps = entry_points(group=group_name)
        except TypeError:
            # compatibility fallback for older Python versions
            eps = entry_points().get(group_name, [])

        for ep in eps:
            try:
                loaded = ep.load()
                instance = loaded()
            except Exception as e:
                print(f"[plugin_discovery] Warning: failed to load entry point '{ep.name}' from '{ep.value}': {e}")
                continue

            if not isinstance(instance, Plugin):
                print(f"[plugin_discovery] Warning: '{ep.name}' is not a Plugin subclass.")
                continue

            if category == "visualization" and not isinstance(instance, VisualizationPlugin):
                print(f"[plugin_discovery] Warning: '{ep.name}' is not a VisualizationPlugin.")
                continue

            if category == "data_source" and not isinstance(instance, DataSourcePlugin):
                print(f"[plugin_discovery] Warning: '{ep.name}' is not a DataSourcePlugin.")
                continue

            try:
                plugin_id = instance.identifier()
                plugin_name = instance.name()
            except Exception as e:
                print(f"[plugin_discovery] Warning: plugin metadata failed for '{ep.name}': {e}")
                continue

            dist_name = None
            try:
                if ep.dist:
                    dist_name = ep.dist.metadata["Name"]
            except Exception:
                dist_name = None

            active = previous_states.get(f"{category}:{plugin_id}", True)

            self.plugins[category][plugin_id] = PluginRecord(
                identifier=plugin_id,
                name=plugin_name,
                category=category,
                instance=instance,
                entry_point_value=ep.value,
                distribution=dist_name,
                active=active,
            )

    def _snapshot_activation_states(self) -> Dict[str, bool]:
        snapshot = {}

        for category, category_plugins in self.plugins.items():
            for plugin_id, record in category_plugins.items():
                snapshot[f"{category}:{plugin_id}"] = record.active

        return snapshot

    # --------------------------------------------------
    # ACCESSORS
    # --------------------------------------------------

    def get_plugins(self):
        """
        Returns raw PluginRecord registry.
        """
        return self.plugins

    def get_plugin_record(self, category: str, plugin_id: str) -> PluginRecord:
        record = self.plugins.get(category, {}).get(plugin_id)

        if record is None:
            raise ValueError(f"Unknown {category} plugin: {plugin_id}")

        return record

    def get_plugin(self, category: str, plugin_id: str, active_only: bool = True) -> Plugin:
        record = self.get_plugin_record(category, plugin_id)

        if active_only and not record.active:
            raise ValueError(f"Plugin '{plugin_id}' is currently deactivated.")

        return record.instance

    def get_active_plugins(self):
        result = {
            "visualization": {},
            "data_source": {},
        }

        for category in result.keys():
            for plugin_id, record in self.plugins[category].items():
                if record.active:
                    result[category][plugin_id] = record.instance

        return result

    def get_plugin_summary(self):
        result = {
            "visualization": [],
            "data_source": [],
        }

        for category in result.keys():
            for plugin_id, record in sorted(self.plugins[category].items(), key=lambda x: x[1].name.lower()):
                result[category].append({
                    "identifier": record.identifier,
                    "name": record.name,
                    "category": record.category,
                    "distribution": record.distribution,
                    "entry_point": record.entry_point_value,
                    "active": record.active,
                })

        return result

    # --------------------------------------------------
    # ACTIVATION / DEACTIVATION
    # --------------------------------------------------

    def activate_plugin(self, category: str, plugin_id: str):
        record = self.get_plugin_record(category, plugin_id)

        if record.active:
            return False

        if hasattr(record.instance, "activate") and callable(record.instance.activate):
            record.instance.activate()

        record.active = True
        return True

    def deactivate_plugin(self, category: str, plugin_id: str):
        record = self.get_plugin_record(category, plugin_id)

        if not record.active:
            return False

        if hasattr(record.instance, "deactivate") and callable(record.instance.deactivate):
            record.instance.deactivate()

        record.active = False
        return True

    def toggle_plugin(self, category: str, plugin_id: str):
        record = self.get_plugin_record(category, plugin_id)

        if record.active:
            self.deactivate_plugin(category, plugin_id)
            return False

        self.activate_plugin(category, plugin_id)
        return True

    # --------------------------------------------------
    # SOURCE TARGETS
    # --------------------------------------------------

    def list_plugin_load_targets(self, project_root: str):
        """
        Returns loadable files/folders under plugins/.
        Paths are relative to project_root.
        """
        plugins_root = os.path.join(project_root, "plugins")
        results = []

        if not os.path.isdir(plugins_root):
            return results

        for root, _, files in os.walk(plugins_root):
            rel_root = os.path.relpath(root, project_root).replace("\\", "/")

            if "nodes.csv" in files and "edges.csv" in files:
                results.append({
                    "value": rel_root,
                    "label": f"{rel_root}/  [CSV folder]"
                })

            for filename in files:
                lower = filename.lower()
                if lower.endswith(".csv") or lower.endswith(".json"):
                    if filename not in ["nodes.csv", "edges.csv", "dir.json"]:
                        rel_path = os.path.join(rel_root, filename).replace("\\", "/")
                        results.append({
                            "value": rel_path,
                            "label": rel_path
                        })

        results.sort(key=lambda x: x["label"].lower())
        return results

    def detect_source_kind(self, project_root: str, source_path: str):
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

    def validate_data_source_choice(self, selected_data_source: str, source_kind: str):
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

    def load_graph_from_selected_source(self, selected_data_source: str, source_path: str, project_root: str):
        source_kind = self.detect_source_kind(project_root, source_path)
        self.validate_data_source_choice(selected_data_source, source_kind)

        abs_source_path = os.path.abspath(os.path.join(project_root, source_path))

        ds_plugin = self.get_plugin("data_source", selected_data_source, active_only=True)

        try:
            return ds_plugin.load(source_path=abs_source_path)
        except TypeError:
            return ds_plugin.load(abs_source_path)