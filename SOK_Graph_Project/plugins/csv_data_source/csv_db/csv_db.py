import csv
import os
import sys
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from api.graph.api.model.node import Node
from api.graph.api.model.edge import Edge
from api.graph.api.model.graph import Graph


class CsvDb:
    """
    CSV data source plugin.

    Supported modes:
    1. separate_files:
       - nodes.csv  -> must contain column 'id'
       - edges.csv  -> must contain columns 'source' and 'target'

    2. single_file:
       - one csv file with node data + reference column
       - example columns: id,name,age,connected_to
       - connected_to can contain one or more ids separated by commas

    Required plugin parameters:
    - mode
    - nodes_path / edges_path   (for separate_files)
    - csv_path                  (for single_file)

    Optional:
    - id_column
    - source_column
    - target_column
    - reference_column
    - delimiter
    """

    DEFAULT_NODES_PATH = os.path.join(
        os.path.dirname(__file__), '..', 'csv_data', 'nodes.csv'
    )
    DEFAULT_EDGES_PATH = os.path.join(
        os.path.dirname(__file__), '..', 'csv_data', 'edges.csv'
    )
    DEFAULT_CSV_PATH = os.path.join(
        os.path.dirname(__file__), '..', 'csv_data', 'csv.csv'
    )

    def __init__(
        self,
        mode="separate_files",
        nodes_path=None,
        edges_path=None,
        csv_path=None,
        id_column="id",
        source_column="source",
        target_column="target",
        reference_column="connected_to",
        delimiter=",",
        directed=True,
    ):
        self.mode = mode
        self.nodes_path = nodes_path or self.DEFAULT_NODES_PATH
        self.edges_path = edges_path or self.DEFAULT_EDGES_PATH
        self.csv_path = csv_path or self.DEFAULT_CSV_PATH

        self.id_column = id_column
        self.source_column = source_column
        self.target_column = target_column
        self.reference_column = reference_column
        self.delimiter = delimiter
        self.directed = directed

    def load(self) -> Graph:
        if self.mode == "separate_files":
            nodes, index_map = self._load_nodes_from_nodes_file()
            edges = self._load_edges_from_edges_file(index_map)
        elif self.mode == "single_file":
            nodes, index_map, edges = self._load_from_single_csv()
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

        cyclic = self._detect_cycle(nodes, edges, directed=self.directed)
        return Graph(nodes=nodes, edges=edges, directed=self.directed, cyclic=cyclic)

    def save(self, graph: Graph) -> None:
        if self.mode == "separate_files":
            self._save_nodes(graph.nodes)
            self._save_edges(graph.edges)
        elif self.mode == "single_file":
            self._save_single_file(graph)
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

    def to_dict(self, graph: Graph) -> dict:
        nodes_list = []
        for node in graph.nodes:
            entry = {"id": node.index}
            entry.update(node.data or {})
            nodes_list.append(entry)

        edges_list = [
            {
                "source": e.node1.index,
                "target": e.node2.index
            }
            for e in graph.edges
            if e.node1 and e.node2
        ]

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "directed": graph.directed,
            "cyclic": graph.cyclic,
        }

    # --------------------------------------------------
    # LOAD: separate_files
    # --------------------------------------------------

    def _load_nodes_from_nodes_file(self):
        nodes = []
        index_map = {}

        with open(self.nodes_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)

            if self.id_column not in reader.fieldnames:
                raise ValueError(f"Missing required column '{self.id_column}' in nodes file.")

            for row in reader:
                node_id = (row.get(self.id_column) or "").strip()
                if not node_id:
                    continue

                data = {
                    k: v for k, v in row.items()
                    if k != self.id_column
                }

                node = Node(data=data, index=node_id)
                nodes.append(node)
                index_map[node_id] = node

        return nodes, index_map

    def _load_edges_from_edges_file(self, index_map):
        edges = []

        with open(self.edges_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)

            required = {self.source_column, self.target_column}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError(
                    f"Edges file must contain columns: {self.source_column}, {self.target_column}"
                )

            for row in reader:
                source_id = (row.get(self.source_column) or "").strip()
                target_id = (row.get(self.target_column) or "").strip()

                if not source_id or not target_id:
                    continue

                if source_id not in index_map:
                    print(f"[CsvDb] Warning: source node '{source_id}' not found. Skipping.")
                    continue
                if target_id not in index_map:
                    print(f"[CsvDb] Warning: target node '{target_id}' not found. Skipping.")
                    continue

                edges.append(Edge(node1=index_map[source_id], node2=index_map[target_id]))

        return edges

    # --------------------------------------------------
    # LOAD: single_file
    # --------------------------------------------------

    def _load_from_single_csv(self):
        nodes = []
        index_map = {}
        raw_rows = []

        with open(self.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)

            if self.id_column not in reader.fieldnames:
                raise ValueError(f"Missing required column '{self.id_column}' in single CSV file.")

            for row in reader:
                node_id = (row.get(self.id_column) or "").strip()
                if not node_id:
                    continue

                data = {
                    k: v for k, v in row.items()
                    if k not in [self.id_column, self.reference_column]
                }

                node = Node(data=data, index=node_id)
                nodes.append(node)
                index_map[node_id] = node
                raw_rows.append(row)

        edges = []
        for row in raw_rows:
            source_id = (row.get(self.id_column) or "").strip()
            refs_raw = (row.get(self.reference_column) or "").strip()

            if not refs_raw:
                continue

            targets = [x.strip() for x in refs_raw.split(",") if x.strip()]
            for target_id in targets:
                if target_id not in index_map:
                    print(f"[CsvDb] Warning: referenced target '{target_id}' not found. Skipping.")
                    continue

                edges.append(Edge(
                    node1=index_map[source_id],
                    node2=index_map[target_id]
                ))

        return nodes, index_map, edges

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    def _save_nodes(self, nodes):
        if not nodes:
            return

        all_keys = []
        for node in nodes:
            for k in (node.data or {}).keys():
                if k not in all_keys:
                    all_keys.append(k)

        with open(self.nodes_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[self.id_column] + all_keys, delimiter=self.delimiter)
            writer.writeheader()
            for node in nodes:
                row = {self.id_column: node.index}
                row.update(node.data or {})
                writer.writerow(row)

    def _save_edges(self, edges):
        with open(self.edges_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[self.source_column, self.target_column],
                delimiter=self.delimiter
            )
            writer.writeheader()
            for edge in edges:
                writer.writerow({
                    self.source_column: edge.node1.index if edge.node1 else "",
                    self.target_column: edge.node2.index if edge.node2 else "",
                })

    def _save_single_file(self, graph):
        if not graph.nodes:
            return

        adjacency = defaultdict(list)
        for edge in graph.edges:
            if edge.node1 and edge.node2:
                adjacency[edge.node1.index].append(edge.node2.index)

        all_keys = []
        for node in graph.nodes:
            for k in (node.data or {}).keys():
                if k not in all_keys:
                    all_keys.append(k)

        fieldnames = [self.id_column] + all_keys + [self.reference_column]

        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
            writer.writeheader()

            for node in graph.nodes:
                row = {self.id_column: node.index}
                row.update(node.data or {})
                row[self.reference_column] = ",".join(adjacency.get(node.index, []))
                writer.writerow(row)

    # --------------------------------------------------
    # CYCLE DETECTION
    # --------------------------------------------------

    def _detect_cycle(self, nodes, edges, directed=True):
        adjacency = defaultdict(list)
        for edge in edges:
            if edge.node1 and edge.node2:
                adjacency[edge.node1.index].append(edge.node2.index)
                if not directed:
                    adjacency[edge.node2.index].append(edge.node1.index)

        visited = set()
        stack = set()

        def dfs(node_id, parent=None):
            visited.add(node_id)
            stack.add(node_id)

            for neigh in adjacency[node_id]:
                if directed:
                    if neigh not in visited:
                        if dfs(neigh):
                            return True
                    elif neigh in stack:
                        return True
                else:
                    if neigh not in visited:
                        if dfs(neigh, node_id):
                            return True
                    elif neigh != parent:
                        return True

            stack.remove(node_id)
            return False

        for node in nodes:
            if node.index not in visited:
                if dfs(node.index):
                    return True

        return False