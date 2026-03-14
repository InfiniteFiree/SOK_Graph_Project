
from .edge import Edge
from .node import Node
from dataclasses import dataclass

@dataclass
class Graph:

    def __init__(self, nodes=None, edges=None, cyclic=None, directed=None):
        self.nodes = nodes
        self.edges = edges
        self.cyclic = cyclic
        self.directed = directed

    @property
    def nodes(self):
        return self._nodes

    @nodes.setter
    def nodes(self, value):
        self._nodes = self._validateNodesList(value)

    @property
    def edges(self):
        return self._edges

    @edges.setter
    def edges(self, value):
        self._edges = self._validateEdgesList(value)

    @property
    def cyclic(self):
        return self._cyclic

    @cyclic.setter
    def cyclic(self, value):
        self._cyclic = value

    @property
    def directed(self):
        return self._directed

    @directed.setter
    def directed(self, value):
        self._directed = value

    def addNode(self, node):
        self.nodes.append(self._validateNode(node))

    def addEdge(self, edge):
        self.edges.append(self._validateEdge(edge))

    def removeEdgeByNodes(self, node1, node2):
        node1_id = self._getNodeId(node1)
        node2_id = self._getNodeId(node2)

        for idx, edge in enumerate(self.edges):
            edge_node1_id = self._getNodeId(edge.node1)
            edge_node2_id = self._getNodeId(edge.node2)

            direct_match = edge_node1_id == node1_id and edge_node2_id == node2_id
            reverse_match = edge_node1_id == node2_id and edge_node2_id == node1_id

            if direct_match or (not self.directed and reverse_match):
                del self.edges[idx]
                return

        raise ValueError("No edge found for the provided two nodes")

    def removeEdge(self, edge):
        for idx, current_edge in enumerate(self.edges):
            if current_edge is edge:
                del self.edges[idx]
                return

        raise ValueError("Provided edge does not exist in graph")

    def removeNode(self, node):
        target_index = None
        for idx, current_node in enumerate(self.nodes):
            if current_node is node:
                target_index = idx
                break

        if target_index is None:
            raise ValueError("Provided node does not exist in graph")

        if self._isNodeConnected(node):
            raise ValueError("Cannot remove node because it has connections")

        del self.nodes[target_index]

    def removeNodeByIndex(self, index):
        target_node = None

        for node in self.nodes:
            if str(getattr(node, "index", None)) == str(index):
                target_node = node
                break

        if target_node is None:
            raise ValueError("No node found for the provided index")

        if self._isNodeConnected(target_node):
            raise ValueError("Cannot remove node because it has connections")

        for idx, current_node in enumerate(self.nodes):
            if current_node is target_node:
                del self.nodes[idx]
                return

        raise ValueError("No node found for the provided index")

    def _isNodeConnected(self, node):
        node_id = self._getNodeId(node)

        for edge in self.edges:
            edge_node1_id = self._getNodeId(edge.node1)
            edge_node2_id = self._getNodeId(edge.node2)

            if edge_node1_id == node_id or edge_node2_id == node_id:
                return True

        return False
    
    def getConnectedOf(self, node):
        node_id = self._getNodeId(node)
        matched_nodes = [
            edge.node2 for edge in self.edges
            if self._getNodeId(edge.node1) == node_id
        ]
        return matched_nodes

    def _validateNodesList(self, nodes):
        if nodes is None:
            return []

        if not isinstance(nodes, list):
            raise TypeError("nodes must be a list of Node objects")

        for node in nodes:
            self._validateNode(node)

        return nodes

    def _validateEdgesList(self, edges):
        if edges is None:
            return []

        if not isinstance(edges, list):
            raise TypeError("edges must be a list of Edge objects")

        for edge in edges:
            self._validateEdge(edge)

        return edges

    def _validateNode(self, node):
        if not isinstance(node, Node):
            raise TypeError("node must be of type Node")

        return node

    def _validateEdge(self, edge):
        if not isinstance(edge, Edge):
            raise TypeError("edge must be of type Edge")

        return edge

    def _getNodeId(self, node):
        if node is None:
            return None
        return str(getattr(node, "index", None))

    def toDict(self):
        return {
            "nodes": [
                {
                    "index": node.index,
                    "data": node.data,
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "node1_index": edge.node1.index if edge.node1 is not None else None,
                    "node2_index": edge.node2.index if edge.node2 is not None else None,
                }
                for edge in self.edges
            ],
            "cyclic": self.cyclic,
            "directed": self.directed,
        }

    def __repr__(self):
        return (
            f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)}, "
            f"cyclic={self.cyclic}, directed={self.directed})"
        )

    def __str__(self):
        return str(self.toDict())