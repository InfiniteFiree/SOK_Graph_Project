
from .node import Node
from dataclasses import dataclass

@dataclass
class Edge:

    def __init__(self, node1=None, node2=None):
        self.node1 = node1
        self.node2 = node2

    @property
    def node1(self):
        return self._node1

    @node1.setter
    def node1(self, value):
        self._node1 = self._validateNode(value)

    @property
    def node2(self):
        return self._node2

    @node2.setter
    def node2(self, value):
        self._node2 = self._validateNode(value)
    
    def swapDirections(self):
        node3=self.node1
        self.node1=self.node2
        self.node2=node3

    def toString(self):
        return f"Edge(node1={self.node1}, node2={self.node2})"

    def __str__(self):
        return self.toString()

    def _validateNode(self, node):
        if node is None:
            return None

        if not isinstance(node, Node):
            raise TypeError("Edge node must be of type Node")

        return node
    
    