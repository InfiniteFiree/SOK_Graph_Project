from api.build.lib.graph.api.services.plugin import VisualizationPlugin
from api.build.lib.graph.api.model.graph import Graph
from core.build.lib.service.use_cases.main_view import MainView


class SimpleVisualizer(VisualizationPlugin):
    def name(self) -> str:
        return "Simple Visualizer"

    def identifier(self) -> str:
        return "simple_visualizer"

    def visualize(self, graph: Graph, **kwargs) -> dict:
        workspace_id = kwargs.get("workspace_id", "default-workspace")

        main_view = MainView(
            graph,
            workspace_id=workspace_id,
            width=kwargs.get("width", 900),
            height=kwargs.get("height", 550),
            link_distance=kwargs.get("link_distance", 140),
            charge_strength=kwargs.get("charge_strength", -500),
            container_id=kwargs.get("container_id", f"simple-visualizer-container-{workspace_id}")
        )

        return {
            "plugin_id": self.identifier(),
            "workspace_id": workspace_id,
            "graph": main_view.render_graph_data(),
            "options": {
                "width": main_view.width,
                "height": main_view.height,
                "link_distance": main_view.link_distance,
                "charge_strength": main_view.charge_strength,
                "container_id": main_view.container_id,
                "node_radius": kwargs.get("node_radius", 28)
            }
        }