class MainView:

    def __init__(self, graph):
        self.graph = graph

    def render(self):

        nodes = []
        edges = []

        for node in self.graph.nodes:
            nodes.append({
                "id": node.index,
                "data": node.data
            })

        for edge in self.graph.edges:
            edges.append({
                "source": edge.node1.index,
                "target": edge.node2.index
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "directed": bool(self.graph.directed),
            "cyclic": bool(self.graph.cyclic)
        }