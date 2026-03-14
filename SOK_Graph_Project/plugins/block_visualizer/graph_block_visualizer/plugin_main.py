from graph.api.services.plugin import VisualizationPlugin
from graph.api.model.graph import Graph
from service.use_cases.main_view import MainView


class BlockVisualizer(VisualizationPlugin):
    def name(self) -> str:
        return "Block Visualizer"

    def identifier(self) -> str:
        return "block_visualizer"

    def visualize(self, graph: Graph, **kwargs) -> dict:
        workspace_id = kwargs.get("workspace_id", "default-workspace")

        main_view = MainView(
            graph,
            workspace_id=workspace_id,
            width=kwargs.get("width", 900),
            height=kwargs.get("height", 550),
            link_distance=kwargs.get("link_distance", 200),
            charge_strength=kwargs.get("charge_strength", -3000),
            container_id=kwargs.get("container_id", f"block-visualizer-{workspace_id}")
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
                "node_radius": 80
            }
        }