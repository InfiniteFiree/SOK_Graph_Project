from __future__ import annotations

import re
import shlex
from typing import TYPE_CHECKING

from api.graph.api.model.edge import Edge
from api.graph.api.model.node import Node

if TYPE_CHECKING:
	from core.service.use_cases.workspace import Workspace


class ConsoleWindow:
	FILTER_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(<=|>=|=|<|>)\s*(.+)$")

	def __init__(self, workspace: Workspace):
		self.workspace = workspace
		self._command_history = []

	@property
	def command_history(self):
		return list(self._command_history)

	def execute(self, command_text: str):
		command_text = (command_text or "").strip()
		if not command_text:
			raise ValueError("Command cannot be empty")

		self._command_history.append(command_text)

		if command_text.startswith("search "):
			query = command_text[len("search "):].strip()
			graph = self.workspace.search_filter.search(query)
			return {
				"display_graph": graph,
				"message": f"Search executed for query: '{query}'",
			}

		if command_text.startswith("filter "):
			expression = command_text[len("filter "):].strip()
			return self._execute_filter(expression)

		parts = shlex.split(command_text)
		if not parts:
			raise ValueError("Command cannot be empty")

		command_name = parts[0].lower()
		args = self._parse_key_value_args(parts[1:])

		if command_name == "create_node":
			return self._create_node(args)
		if command_name == "delete_node":
			return self._delete_node(args)
		if command_name == "edit_node":
			return self._edit_node(args)
		if command_name == "create_edge":
			return self._create_edge(args)
		if command_name == "delete_edge":
			return self._delete_edge(args)

		raise ValueError(f"Unsupported command: {command_name}")

	def _execute_filter(self, expression: str):
		match = self.FILTER_PATTERN.match(expression)
		if match is None:
			raise ValueError("Invalid filter syntax. Use: filter age>=20")

		attribute, operator, value = match.groups()
		graph = self.workspace.search_filter.filter(attribute, operator, value)
		return {
			"display_graph": graph,
			"message": f"Filter applied: {attribute}{operator}{value}",
		}

	def _create_node(self, args: dict):
		node_id = self._required_arg(args, "id")
		graph = self.workspace.graph

		if self._find_node(graph, node_id) is not None:
			raise ValueError(f"Node with id '{node_id}' already exists")

		node_data = {k: v for k, v in args.items() if k != "id"}
		graph.addNode(Node(data=node_data, index=node_id))
		self.workspace.search_filter.set_source_graph(graph)

		return {
			"display_graph": self.workspace.search_filter.filtered_graph,
			"message": f"Created node {node_id}",
		}

	def _delete_node(self, args: dict):
		node_id = self._required_arg(args, "id")
		graph = self.workspace.graph
		node = self._find_node(graph, node_id)

		if node is None:
			raise ValueError(f"Node with id '{node_id}' was not found")

		if self._node_has_edges(graph, node):
			raise ValueError("Cannot delete node because it is part of an existing edge")

		graph.removeNode(node)
		self.workspace.search_filter.set_source_graph(graph)

		return {
			"display_graph": self.workspace.search_filter.filtered_graph,
			"message": f"Deleted node {node_id}",
		}

	def _edit_node(self, args: dict):
		node_id = self._required_arg(args, "id")
		graph = self.workspace.graph
		node = self._find_node(graph, node_id)

		if node is None:
			raise ValueError(f"Node with id '{node_id}' was not found")

		updates = {k: v for k, v in args.items() if k != "id"}
		if not updates:
			raise ValueError("edit_node requires at least one attribute to update")

		node.data.update(updates)
		self.workspace.search_filter.set_source_graph(graph)

		return {
			"display_graph": self.workspace.search_filter.filtered_graph,
			"message": f"Edited node {node_id}",
		}

	def _create_edge(self, args: dict):
		node1_id = self._required_arg(args, "n1")
		node2_id = self._required_arg(args, "n2")
		graph = self.workspace.graph

		node1 = self._find_node(graph, node1_id)
		node2 = self._find_node(graph, node2_id)

		if node1 is None or node2 is None:
			raise ValueError("Both nodes must exist before creating an edge")

		if self._find_edge(graph, node1, node2) is not None:
			raise ValueError("Edge already exists")

		graph.addEdge(Edge(node1=node1, node2=node2))
		self.workspace.search_filter.set_source_graph(graph)

		return {
			"display_graph": self.workspace.search_filter.filtered_graph,
			"message": f"Created edge {node1_id}->{node2_id}",
		}

	def _delete_edge(self, args: dict):
		node1_id = self._required_arg(args, "n1")
		node2_id = self._required_arg(args, "n2")
		graph = self.workspace.graph

		node1 = self._find_node(graph, node1_id)
		node2 = self._find_node(graph, node2_id)

		if node1 is None or node2 is None:
			raise ValueError("Both nodes must exist before deleting an edge")

		graph.removeEdgeByNodes(node1, node2)
		self.workspace.search_filter.set_source_graph(graph)

		return {
			"display_graph": self.workspace.search_filter.filtered_graph,
			"message": f"Deleted edge {node1_id}->{node2_id}",
		}

	def _required_arg(self, args: dict, name: str):
		value = args.get(name)
		if value is None or str(value).strip() == "":
			raise ValueError(f"Missing required argument: {name}")
		return self._normalize_scalar(value)

	def _parse_key_value_args(self, arg_tokens):
		parsed = {}
		for token in arg_tokens:
			if "=" not in token:
				raise ValueError(f"Invalid argument '{token}'. Use key=value format")
			key, value = token.split("=", 1)
			key = key.strip()
			value = value.strip()
			if not key:
				raise ValueError(f"Invalid argument '{token}'. Key cannot be empty")
			parsed[key] = self._normalize_scalar(value)
		return parsed

	def _normalize_scalar(self, value):
		text = str(value)
		if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
			try:
				return int(text)
			except ValueError:
				return text
		return text

	def _find_node(self, graph, node_id):
		for node in graph.nodes:
			if str(node.index) == str(node_id):
				return node
		return None

	def _find_edge(self, graph, node1, node2):
		node1_id = self._node_id(node1)
		node2_id = self._node_id(node2)

		for edge in graph.edges:
			edge_node1_id = self._node_id(edge.node1)
			edge_node2_id = self._node_id(edge.node2)

			direct_match = edge_node1_id == node1_id and edge_node2_id == node2_id
			reverse_match = edge_node1_id == node2_id and edge_node2_id == node1_id

			if direct_match:
				return edge

			if not getattr(graph, "directed", False) and reverse_match:
				return edge

		return None

	def _node_has_edges(self, graph, node):
		node_id = self._node_id(node)

		for edge in graph.edges:
			edge_node1_id = self._node_id(edge.node1)
			edge_node2_id = self._node_id(edge.node2)

			if edge_node1_id == node_id or edge_node2_id == node_id:
				return True
		return False

	def _node_id(self, node):
		if node is None:
			return None
		return str(getattr(node, "index", None))
