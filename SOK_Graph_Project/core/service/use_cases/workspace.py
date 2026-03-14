import uuid

from core.service.use_cases.graph_search_filter import GraphSearchFilter


class Workspace:
    def __init__(self, graph, name=None, visualizer_type="simple_visualizer",
                 data_source="csv", source_path=""):
        self.id = str(uuid.uuid4())
        self.name = name or f"Workspace {self.id[:8]}"
        self.graph = graph
        self.visualizer_type = visualizer_type
        self.data_source = data_source
        self.source_path = source_path
        self.search_filter = GraphSearchFilter()
        self.search_filter.set_source_graph(graph)