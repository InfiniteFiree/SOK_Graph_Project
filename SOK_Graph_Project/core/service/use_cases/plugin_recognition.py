from importlib.metadata import entry_points
from typing import List

from block_visualizer.block_visualizer import BlockVisualizer
from simple_visualizer.simple_visualizer import SimpleVisualizer
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


def get_visualizer(plugin_type: str):
    """Vrati instancu vizualizera na osnovu tipa plugin-a."""
    if plugin_type == "block":
        return BlockVisualizer()
    elif plugin_type == "simple":
        return SimpleVisualizer()
    else:
        return BlockVisualizer()

    
def recognize_plugin(user_preference: str = None):
    """
    Prepoznaje koji vizualizer treba koristiti.
    Ako nije prosleđen preference, vraća default (block).
    """
    plugin_type = user_preference or "block"
    return get_visualizer(plugin_type)