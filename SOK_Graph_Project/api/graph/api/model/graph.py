
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

    def removeEdgesByNode(self, node):
        matched_edges = [
            edge for edge in self.edges
            if edge.getNode1() == node or edge.getNode2() == node
        ]

        if not matched_edges:
            raise ValueError("No edges found for the provided node")

        for edge in matched_edges:
            self.edges.remove(edge)

    def removeEdgeByNodes(self, node1, node2):
        matched_edges = [
            edge for edge in self.edges
            if (edge.getNode1() == node1 and edge.getNode2() == node2)
            or (edge.getNode1() == node2 and edge.getNode2() == node1)
        ]

        if not matched_edges:
            raise ValueError("No edge found for the provided two nodes")

        for edge in matched_edges:
            self.edges.remove(edge)

    def removeEdge(self, edge):
        if edge not in self.edges:
            raise ValueError("Provided edge does not exist in graph")

        self.edges.remove(edge)

    def removeNode(self, node):
        if node not in self.nodes:
            raise ValueError("Provided node does not exist in graph")

        if self._isNodeConnected(node):
            raise ValueError("Cannot remove node because it has connections")

        self.nodes.remove(node)

    def removeNodeByIndex(self, index):
        target_node = None

        for node in self.nodes:
            if node.getIndex() == index:
                target_node = node
                break

        if target_node is None:
            raise ValueError("No node found for the provided index")

        if self._isNodeConnected(target_node):
            raise ValueError("Cannot remove node because it has connections")

        self.nodes.remove(target_node)

    def _isNodeConnected(self, node):
        for edge in self.edges:
            if edge.getNode1() == node or edge.getNode2() == node:
                return True

        return False
    
    def getConnectedOf(self, node):
        matched_nodes = [
            edge.getNode2() for edge in self.edges
            if edge.getNode1() == node
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