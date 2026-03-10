from importlib.metadata import entry_points
from typing import List

from api.graph.api.services.plugin import DataSourcePlugin, VisualizationPlugin


class PluginService(object):

    def __init__(self):
        self.data_plugins: dict[str,List[DataSourcePlugin]] = {}
        self.vis_plugins: dict[str,List[VisualizationPlugin]] = {}

    def load_plugins(self, group: str):
        """
        Dynamically loads plugins based on entrypoint group.
        """
        if group == "data_source":
            self.data_plugins[group] = []
            for ep in entry_points(group=group):
                p = ep.load()
                plugin: DataSourcePlugin = p()
                self.data_plugins[group].append(plugin)
        elif group == "visualization":
            self.vis_plugins[group] = []
            for ep in entry_points(group=group):
                p = ep.load()
                plugin: VisualizationPlugin = p()
                self.vis_plugins[group].append(plugin)