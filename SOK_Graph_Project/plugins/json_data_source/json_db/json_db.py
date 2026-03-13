import os
import json
from api.graph.api.model.edge import Edge
from api.graph.api.model.graph import Graph
from api.graph.api.model.node import Node

class JSONRepository:

    def __init__(self, file):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.data_dir = os.path.abspath(os.path.join(self.base_dir, "..", "json_data"))
        self.file = self._resolve_path(file)

    def _resolve_path(self, file):
        if not file:
            file = "json.json"

        if os.path.isabs(file):
            return file

        normalized = os.path.normpath(file)
        return os.path.abspath(os.path.join(self.data_dir, normalized))

    # @staticmethod
    # def graph_to_dict(graph):
    #     if not isinstance(graph, Graph):
    #         raise TypeError("graph must be an instance of Graph")

    #     nodes_payload = []
    #     for node in graph.nodes:
    #         nodes_payload.append(
    #             {
    #                 "index": node.index,
    #                 "data": node.data
    #             }
    #         )

    #     edges_payload = []
    #     for edge in graph.edges:
    #         edges_payload.append(
    #             {
    #                 "node1_index": edge.node1.index if edge.node1 is not None else None,
    #                 "node2_index": edge.node2.index if edge.node2 is not None else None
    #             }
    #         )

    #     return {
    #         "nodes": nodes_payload,
    #         "edges": edges_payload,
    #         "cyclic": graph.cyclic,
    #         "directed": graph.directed
    #     }

    @staticmethod
    def dict_to_graph(data):
        if not isinstance(data, dict):
            raise TypeError("JSON data must be a dictionary")

        raw_nodes = data.get("nodes", [])
        raw_edges = data.get("edges", [])

        if not isinstance(raw_nodes, list):
            raise ValueError("'nodes' must be a list")
        if not isinstance(raw_edges, list):
            raise ValueError("'edges' must be a list")

        nodes = []
        nodes_by_index = {}
        for node_data in raw_nodes:
            if not isinstance(node_data, dict):
                raise ValueError("Each node must be an object")

            node = Node(
                data=node_data.get("data", {}),
                index=node_data.get("index")
            )
            nodes.append(node)
            nodes_by_index[node.index] = node

        edges = []
        for edge_data in raw_edges:
            if not isinstance(edge_data, dict):
                raise ValueError("Each edge must be an object")

            node1_index = edge_data.get("node1_index")
            node2_index = edge_data.get("node2_index")

            if node1_index is not None and node1_index not in nodes_by_index:
                raise ValueError(f"Edge references unknown node index: {node1_index}")
            if node2_index is not None and node2_index not in nodes_by_index:
                raise ValueError(f"Edge references unknown node index: {node2_index}")

            edge = Edge(
                node1=nodes_by_index.get(node1_index),
                node2=nodes_by_index.get(node2_index)
            )
            edges.append(edge)

        return Graph(
            nodes=nodes,
            edges=edges,
            cyclic=data.get("cyclic"),
            directed=data.get("directed")
        )

    # @classmethod
    # def graph_from_json_string(cls, json_string):
    #     data = json.loads(json_string)
    #     return cls.dict_to_graph(data)

    # def save_to_file(self, graph):
    #     try:
    #         if not isinstance(graph, Graph):
    #             raise TypeError("graph must be an instance of Graph")

    #         data = self.graph_to_dict(graph)
    #         directory = os.path.dirname(self.file)
    #         if directory:
    #             os.makedirs(directory, exist_ok=True)

    #         with open(self.file, 'w', encoding='utf-8') as file:
    #             json.dump(data, file, indent=4, ensure_ascii=False)
    #         return True
    #     except (TypeError, ValueError) as e:
    #         print(f"Serialization error: {e}")
    #         return False
    #     except OSError as e:
    #         print(f"File write error: {e}")
    #         return False


    def read_from_file(self):
        if not os.path.exists(self.file):
            print(f"Error: File '{self.file}' does not exist.")
            return None
        try:
            with open(self.file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return self.dict_to_graph(data)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format. {e}")
        except PermissionError:
            print(f"Error: Permission denied for file '{self.file}'.")
        except (TypeError, ValueError) as e:
            print(f"Deserialization error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        return None
