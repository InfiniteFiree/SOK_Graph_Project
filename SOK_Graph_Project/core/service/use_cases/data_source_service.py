import json
import os
from collections import defaultdict

from graph.api.model.node import Node
from graph.api.model.edge import Edge
from graph.api.model.graph import Graph


class DataSourceService:

    # --------------------------------------------------
    # PATH VALIDATION
    # --------------------------------------------------

    @staticmethod
    def require_source_path(source_path):
        if not source_path:
            raise ValueError("source_path is required")
        return os.path.abspath(source_path)

    @staticmethod
    def require_existing_file(source_path, extension=None):
        source_path = DataSourceService.require_source_path(source_path)

        if not os.path.isfile(source_path):
            raise ValueError(f"File does not exist: {source_path}")

        if extension and not source_path.lower().endswith(extension.lower()):
            raise ValueError(f"Expected a {extension} file")

        return source_path

    @staticmethod
    def require_existing_directory(source_path):
        source_path = DataSourceService.require_source_path(source_path)

        if not os.path.isdir(source_path):
            raise ValueError(f"Directory does not exist: {source_path}")

        return source_path

    @staticmethod
    def require_files(directory, required_files):
        missing = [
            f for f in required_files
            if not os.path.isfile(os.path.join(directory, f))
        ]

        if missing:
            raise ValueError(
                f"Directory '{directory}' missing files: {', '.join(missing)}"
            )

        return {
            f: os.path.join(directory, f)
            for f in required_files
        }

    # --------------------------------------------------
    # JSON HELPERS
    # --------------------------------------------------

    @staticmethod
    def read_json(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def write_json(file_path, payload):
        directory = os.path.dirname(file_path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

    # --------------------------------------------------
    # GRAPH BUILDING
    # --------------------------------------------------

    @staticmethod
    def build_graph(nodes, edges, directed=True):

        node_objects = []
        node_map = {}

        for node in nodes:
            node_obj = Node(
                index=node["index"],
                data=node.get("data", {})
            )
            node_objects.append(node_obj)
            node_map[node_obj.index] = node_obj

        edge_objects = []

        for source, target in edges:

            if source not in node_map:
                raise ValueError(f"Unknown node index: {source}")

            if target not in node_map:
                raise ValueError(f"Unknown node index: {target}")

            edge_objects.append(
                Edge(
                    node1=node_map[source],
                    node2=node_map[target]
                )
            )

        cyclic = DataSourceService.detect_cycle(
            node_objects,
            edge_objects,
            directed
        )

        return Graph(
            nodes=node_objects,
            edges=edge_objects,
            directed=directed,
            cyclic=cyclic
        )

    # --------------------------------------------------
    # GRAPH SERIALIZATION
    # --------------------------------------------------

    @staticmethod
    def graph_to_dict(graph):

        return {
            "nodes": [
                {
                    "index": node.index,
                    "data": node.data or {}
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "node1_index": edge.node1.index if edge.node1 else None,
                    "node2_index": edge.node2.index if edge.node2 else None
                }
                for edge in graph.edges
            ],
            "directed": graph.directed,
            "cyclic": graph.cyclic
        }

    @staticmethod
    def dict_to_graph(data):

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        edge_pairs = [
            (e.get("node1_index"), e.get("node2_index"))
            for e in edges
        ]

        return DataSourceService.build_graph(
            nodes,
            edge_pairs,
            directed=data.get("directed", True)
        )

    # --------------------------------------------------
    # CYCLE DETECTION
    # --------------------------------------------------

    @staticmethod
    def detect_cycle(nodes, edges, directed=True):

        adjacency = defaultdict(list)

        for edge in edges:
            adjacency[edge.node1.index].append(edge.node2.index)

            if not directed:
                adjacency[edge.node2.index].append(edge.node1.index)

        visited = set()
        stack = set()

        def dfs(node, parent=None):

            visited.add(node)
            stack.add(node)

            for neighbor in adjacency[node]:

                if directed:

                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True

                    elif neighbor in stack:
                        return True

                else:

                    if neighbor not in visited:
                        if dfs(neighbor, node):
                            return True

                    elif neighbor != parent:
                        return True

            stack.remove(node)

            return False

        for node in nodes:

            if node.index not in visited:
                if dfs(node.index):
                    return True

        return False