from __future__ import annotations

from api.graph.api.model.graph import Graph


class GraphSearchFilter:
	def __init__(self):
		self._source_graph = Graph()
		self._filtered_graph = Graph()

	@property
	def filtered_graph(self) -> Graph:
		return self._filtered_graph

	def set_source_graph(self, graph: Graph) -> None:
		self._source_graph = graph if graph is not None else Graph()
		self._filtered_graph = self._clone_graph(self._source_graph)

	def clear_filters(self, graph: Graph) -> Graph:
		self.set_source_graph(graph)
		return self.filtered_graph

	def filter(self, attribute: str, operator: str, value: str) -> Graph:
		attribute = (attribute or "").strip()

		if not attribute:
			self._filtered_graph = self._clone_graph(self._filtered_graph)
			return self.filtered_graph

		matched_nodes = []
		for node in self.filtered_graph.nodes:
			node_data = node.data if isinstance(node.data, dict) else {}
			if attribute not in node_data:
				continue

			node_value = node_data.get(attribute)
			if self._matches_operator(node_value, operator, value):
				matched_nodes.append(node)

		self._filtered_graph = self._build_subgraph(self.filtered_graph, matched_nodes)
		return self.filtered_graph

	def search(self, query: str) -> Graph:
		query = (query or "").strip().lower()

		if not query:
			return self._clone_graph(self.filtered_graph)

		matched_nodes = []
		for node in self.filtered_graph.nodes:
			node_data = node.data if isinstance(node.data, dict) else {}
			if self._node_contains(node_data, query):
				matched_nodes.append(node)

		return self._build_subgraph(self.filtered_graph, matched_nodes)

	def _build_subgraph(self, graph: Graph, nodes: list) -> Graph:
		node_ids = {str(node.index) for node in nodes}
		edges = []

		for edge in graph.edges:
			node1 = edge.node1
			node2 = edge.node2
			if node1 is None or node2 is None:
				continue

			if str(node1.index) in node_ids and str(node2.index) in node_ids:
				edges.append(edge)

		return Graph(
			nodes=list(nodes),
			edges=edges,
			cyclic=graph.cyclic,
			directed=graph.directed,
		)

	def _clone_graph(self, graph: Graph) -> Graph:
		if graph is None:
			return Graph()

		return Graph(
			nodes=list(graph.nodes or []),
			edges=list(graph.edges or []),
			cyclic=graph.cyclic,
			directed=graph.directed,
		)

	def _matches_operator(self, node_value, operator: str, expected_value: str) -> bool:
		operator = (operator or "=").strip()

		if operator == "=":
			return str(node_value) == str(expected_value)

		left_number = self._to_float(node_value)
		right_number = self._to_float(expected_value)

		if left_number is not None and right_number is not None:
			if operator == "<":
				return left_number < right_number
			if operator == "<=":
				return left_number <= right_number
			if operator == ">":
				return left_number > right_number
			if operator == ">=":
				return left_number >= right_number

		left_text = str(node_value)
		right_text = str(expected_value)

		if operator == "<":
			return left_text < right_text
		if operator == "<=":
			return left_text <= right_text
		if operator == ">":
			return left_text > right_text
		if operator == ">=":
			return left_text >= right_text

		return False

	def _to_float(self, value):
		try:
			return float(value)
		except (TypeError, ValueError):
			return None

	def _node_contains(self, node_data: dict, query: str) -> bool:
		for key, value in node_data.items():
			if query in str(key).lower() or query in str(value).lower():
				return True

		return False
