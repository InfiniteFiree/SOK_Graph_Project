import json


class MainView:
    def __init__(self, graph, workspace_id="default-workspace", **kwargs):
        self.graph = graph
        self.workspace_id = workspace_id
        self.width = kwargs.get("width", 900)
        self.height = kwargs.get("height", 550)
        self.link_distance = kwargs.get("link_distance", 140)
        self.charge_strength = kwargs.get("charge_strength", -500)
        self.container_id = kwargs.get("container_id", f"main-view-{workspace_id}")

    def render_graph_data(self):
        nodes = []
        edges = []

        for node in self.graph.nodes or []:
            nodes.append({
                "id": str(node.index),
                "data": node.data if isinstance(node.data, dict) else {}
            })

        for edge in self.graph.edges or []:
            if edge.node1 is None or edge.node2 is None:
                continue

            edges.append({
                "source": str(edge.node1.index),
                "target": str(edge.node2.index)
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "directed": bool(getattr(self.graph, "directed", False)),
            "cyclic": bool(getattr(self.graph, "cyclic", False))
        }

    def render_context(self):
        return {
            "workspace_id_json": json.dumps(str(self.workspace_id)),
            "graph_json": json.dumps(self.render_graph_data()),
            "width": self.width,
            "height": self.height,
            "link_distance": self.link_distance,
            "charge_strength": self.charge_strength,
            "container_id": self.container_id,
        }

    def render_base_style(self):
        return f"""
<style>
    #{self.container_id} {{
        position: relative;
        width: 100%;
        min-height: {self.height}px;
        border: 1px solid #ccc;
        border-radius: 8px;
        background: #fff;
        overflow: hidden;
    }}

    #{self.container_id} .main-view-canvas {{
        width: 100%;
        height: {self.height}px;
    }}

    #{self.container_id} svg {{
        width: 100%;
        height: 100%;
        display: block;
        cursor: grab;
    }}

    #{self.container_id} svg:active {{
        cursor: grabbing;
    }}

    #{self.container_id} .link {{
        stroke: #999;
        stroke-opacity: 0.6;
        stroke-width: 2px;
    }}
</style>
"""

    def render_base_container(self):
        return f"""
<div id="{self.container_id}" class="main-view-wrapper">
    <div class="main-view-canvas"></div>
</div>
"""

    def render_base_script_start(self):
        ctx = self.render_context()
        return f"""
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
(function() {{
    const workspaceId = {ctx["workspace_id_json"]};
    const graphData = {ctx["graph_json"]};
    const wrapper = document.getElementById("{ctx["container_id"]}");
    if (!wrapper) return;

    const canvas = wrapper.querySelector(".main-view-canvas");
    if (!canvas) return;

    window.workspaceGraphStates = window.workspaceGraphStates || {{}};

    d3.select(canvas).selectAll("svg").remove();

    const width = canvas.clientWidth || {ctx["width"]};
    const height = {ctx["height"]};

    let selectedNodeId = null;

    const svg = d3.select(canvas)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", `0 0 ${{width}} ${{height}}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const defs = svg.append("defs");

    defs.append("marker")
        .attr("id", `arrowhead-${{workspaceId}}`)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 40)
        .attr("refY", 0)
        .attr("markerWidth", 7)
        .attr("markerHeight", 7)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#999");

    const graphLayer = svg.append("g");

    const zoom = d3.zoom()
        .scaleExtent([0.07, 4])
        .on("zoom", function(event) {{
            graphLayer.attr("transform", event.transform);
            notifyBirdView();
        }});

    svg.call(zoom);

    const simulation = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.edges)
            .id(d => d.id)
            .distance({ctx["link_distance"]}))
        .force("charge", d3.forceManyBody().strength({ctx["charge_strength"]}))
        .force("center", d3.forceCenter(width / 2, height / 2));

    const links = graphLayer.append("g")
        .selectAll("line")
        .data(graphData.edges)
        .enter()
        .append("line")
        .attr("class", "link")
        .attr("marker-end", graphData.directed ? `url(#arrowhead-${{workspaceId}})` : null);

    function dragstarted(event, d) {{
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }}

    function dragged(event, d) {{
        d.fx = event.x;
        d.fy = event.y;
        notifyBirdView();
    }}

    function dragended(event, d) {{
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
        notifyBirdView();
    }}

    function focusNode(nodeId) {{
        const targetNode = graphData.nodes.find(n => String(n.id) === String(nodeId));
        if (!targetNode) return;
        if (!Number.isFinite(targetNode.x) || !Number.isFinite(targetNode.y)) return;

        const currentTransform = d3.zoomTransform(svg.node());
        const currentScale = currentTransform.k || 1;

        const targetX = width / 2 - targetNode.x * currentScale;
        const targetY = height / 2 - targetNode.y * currentScale;

        const newTransform = d3.zoomIdentity
            .translate(targetX, targetY)
            .scale(currentScale);

        svg.transition()
            .duration(400)
            .call(zoom.transform, newTransform);
    }}

    function findNodeById(nodeId) {{
        return graphData.nodes.find(n => String(n.id) === String(nodeId)) || null;
    }}

    function notifyBirdView(nodeSizeInfo = {{ nodeWidth: 56, nodeHeight: 56, nodeRadius: 28 }}) {{
        window.workspaceGraphStates[workspaceId] = {{
            nodes: graphData.nodes,
            edges: graphData.edges,
            width: width,
            height: height,
            nodeWidth: nodeSizeInfo.nodeWidth,
            nodeHeight: nodeSizeInfo.nodeHeight,
            nodeRadius: nodeSizeInfo.nodeRadius,
            selectedNodeId: selectedNodeId,
            transform: d3.zoomTransform(svg.node())
        }};

        window.dispatchEvent(new CustomEvent("main-view-updated", {{
            detail: {{
                workspaceId: workspaceId
            }}
        }}));
    }}
"""

    def render_base_script_end(self):
        return """
})();
</script>
"""