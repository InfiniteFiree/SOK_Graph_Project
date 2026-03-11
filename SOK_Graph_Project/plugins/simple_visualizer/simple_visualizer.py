import json
from typing import Any

from api.graph.api.services.plugin import VisualizationPlugin
from api.graph.api.model.graph import Graph


class SimpleVisualizer(VisualizationPlugin):
    def name(self) -> str:
        return "Simple Visualizer"

    def identifier(self) -> str:
        return "simple_visualizer"

    def visualize(self, graph: Graph, **kwargs) -> str:
        width = kwargs.get("width", 900)
        height = kwargs.get("height", 550)
        link_distance = kwargs.get("link_distance", 140)
        charge_strength = kwargs.get("charge_strength", -500)
        node_radius = kwargs.get("node_radius", 28)

        graph_dict = self._graph_to_d3_dict(graph)
        graph_json = json.dumps(graph_dict)

        container_id = kwargs.get("container_id", "simple-visualizer-container")
        modal_id = kwargs.get("modal_id", "simple-visualizer-modal")
        overlay_id = kwargs.get("overlay_id", "simple-visualizer-overlay")

        return f"""
<div id="{container_id}" class="simple-visualizer-wrapper">
    <div class="simple-visualizer-canvas"></div>

    <div id="{overlay_id}" class="simple-visualizer-overlay" style="display: none;"></div>
    <div id="{modal_id}" class="simple-visualizer-modal" style="display: none;">
        <div class="simple-visualizer-modal-header">
            <span>Node Details</span>
            <button type="button" class="simple-visualizer-close-btn">&times;</button>
        </div>
        <div class="simple-visualizer-modal-body"></div>
    </div>
</div>

<style>
    #{container_id} {{
        position: relative;
        width: 100%;
        min-height: {height}px;
        border: 1px solid #ccc;
        border-radius: 8px;
        background: #fff;
        overflow: hidden;
    }}

    #{container_id} .simple-visualizer-canvas {{
        width: 100%;
        height: {height}px;
    }}

    #{container_id} .simple-visualizer-overlay {{
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.25);
        z-index: 10;
    }}

    #{container_id} .simple-visualizer-modal {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: min(420px, 90%);
        background: white;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        z-index: 11;
        overflow: hidden;
        font-family: Arial, sans-serif;
    }}

    #{container_id} .simple-visualizer-modal-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 14px;
        border-bottom: 1px solid #e5e5e5;
        background: #fafafa;
        font-weight: bold;
    }}

    #{container_id} .simple-visualizer-modal-body {{
        padding: 14px;
        max-height: 300px;
        overflow: auto;
        font-size: 14px;
    }}

    #{container_id} .simple-visualizer-close-btn {{
        border: none;
        background: transparent;
        font-size: 20px;
        cursor: pointer;
        line-height: 1;
    }}

    #{container_id} .simple-visualizer-detail-table {{
        width: 100%;
        border-collapse: collapse;
    }}

    #{container_id} .simple-visualizer-detail-table td {{
        border-bottom: 1px solid #f0f0f0;
        padding: 6px 4px;
        vertical-align: top;
    }}

    #{container_id} .simple-visualizer-detail-key {{
        font-weight: bold;
        width: 35%;
        white-space: nowrap;
    }}

    #{container_id} svg {{
        width: 100%;
        height: 100%;
        display: block;
        cursor: grab;
    }}

    #{container_id} svg:active {{
        cursor: grabbing;
    }}

    #{container_id} .link {{
        stroke: #999;
        stroke-opacity: 0.6;
        stroke-width: 2px;
    }}

    #{container_id} .node-circle {{
        fill: #f8f8f8;
        stroke: #444;
        stroke-width: 2px;
        cursor: pointer;
    }}

    #{container_id} .node-circle.selected {{
        fill: #4a90e2;
        stroke: #1f5fa8;
        stroke-width: 3px;
    }}

    #{container_id} .node-label {{
        font-size: 12px;
        font-family: Arial, sans-serif;
        pointer-events: none;
        user-select: none;
        text-anchor: middle;
        dominant-baseline: middle;
        fill: #111;
    }}
</style>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
(function() {{
    const graphData = {graph_json};
    const wrapper = document.getElementById("{container_id}");
    const canvas = wrapper.querySelector(".simple-visualizer-canvas");
    const modal = document.getElementById("{modal_id}");
    const overlay = document.getElementById("{overlay_id}");
    const closeBtn = wrapper.querySelector(".simple-visualizer-close-btn");
    const modalBody = wrapper.querySelector(".simple-visualizer-modal-body");

    d3.select(canvas).selectAll("svg").remove();

    const width = canvas.clientWidth || {width};
    const height = {height};
    const nodeRadius = {node_radius};

    let selectedNodeId = null;

    const svg = d3.select(canvas)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", `0 0 ${{width}} ${{height}}`)
        .attr("preserveAspectRatio", "xMidYMid meet");

    const graphLayer = svg.append("g");

    const zoom = d3.zoom()
        .scaleExtent([0.2, 4])
        .on("zoom", function(event) {{
            graphLayer.attr("transform", event.transform);
            notifyBirdView();
        }});

    svg.call(zoom);

    const simulation = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.edges)
            .id(d => d.id)
            .distance({link_distance}))
        .force("charge", d3.forceManyBody().strength({charge_strength}))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(nodeRadius + 8));

    const links = graphLayer.append("g")
        .selectAll("line")
        .data(graphData.edges)
        .enter()
        .append("line")
        .attr("class", "link");

    const nodes = graphLayer.append("g")
        .selectAll("g")
        .data(graphData.nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    nodes.append("circle")
        .attr("class", "node-circle")
        .attr("r", nodeRadius)
        .on("click", function(event, d) {{
            event.stopPropagation();
            selectNode(d.id);
            showNodeDetails(d);
            notifyBirdView();

            window.dispatchEvent(new CustomEvent("graph-node-selected", {{
                detail: {{
                    nodeId: d.id,
                    source: "{container_id}"
                }}
            }}));
        }});

    nodes.append("text")
        .attr("class", "node-label")
        .text(d => `id=${{d.id}}`);

    simulation.on("tick", () => {{
        links
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        nodes.attr("transform", d => `translate(${{d.x}}, ${{d.y}})`);

        notifyBirdView();
    }});

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

    function selectNode(nodeId) {{
        selectedNodeId = String(nodeId);

        nodes.each(function(d) {{
            const circle = this.querySelector(".node-circle");
            if (!circle) return;

            if (String(d.id) === selectedNodeId) {{
                circle.classList.add("selected");
            }} else {{
                circle.classList.remove("selected");
            }}
        }});
    }}

    function focusNode(nodeId) {{
        const targetNode = graphData.nodes.find(n => String(n.id) === String(nodeId));
        if (!targetNode) return;

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

    function showNodeDetails(nodeData) {{
        const rows = Object.entries(nodeData.data || {{}})
            .map(([key, value]) => `
                <tr>
                    <td class="simple-visualizer-detail-key">${{escapeHtml(String(key))}}</td>
                    <td>${{escapeHtml(String(value))}}</td>
                </tr>
            `)
            .join("");

        modalBody.innerHTML = `
            <table class="simple-visualizer-detail-table">
                <tr>
                    <td class="simple-visualizer-detail-key">id</td>
                    <td>${{escapeHtml(String(nodeData.id))}}</td>
                </tr>
                ${{rows}}
            </table>
        `;

        overlay.style.display = "block";
        modal.style.display = "block";
    }}

    function hideModal() {{
        overlay.style.display = "none";
        modal.style.display = "none";
    }}

    function escapeHtml(value) {{
        return value
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }}

    function notifyBirdView() {{
        window.mainGraphState = {{
            nodes: graphData.nodes,
            edges: graphData.edges,
            width: width,
            height: height,
            nodeWidth: nodeRadius * 2,
            nodeHeight: nodeRadius * 2,
            nodeRadius: nodeRadius,
            selectedNodeId: selectedNodeId,
            transform: d3.zoomTransform(svg.node())
        }};

        window.dispatchEvent(new CustomEvent("main-view-updated"));
    }}

    closeBtn.addEventListener("click", hideModal);
    overlay.addEventListener("click", hideModal);

    svg.on("click", function(event) {{
        if (event.target === svg.node()) {{
            hideModal();
        }}
    }});

    window.addEventListener("graph-node-selected", function(event) {{
        const detail = event.detail || {{}};
        if (detail.nodeId == null) return;

        if (detail.source === "{container_id}") {{
            return;
        }}

        selectNode(detail.nodeId);

        if (detail.panTo) {{
            focusNode(detail.nodeId);
        }}

        const selectedNode = findNodeById(detail.nodeId);
        if (selectedNode && detail.source === "tree-view") {{
            showNodeDetails(selectedNode);
        }}

        notifyBirdView();
    }});

    notifyBirdView();
}})();
</script>
"""

    def _graph_to_d3_dict(self, graph: Graph) -> dict[str, Any]:
        nodes = []
        edges = []

        if graph is None:
            return {"nodes": [], "edges": []}

        for node in graph.nodes or []:
            nodes.append({
                "id": str(node.index),
                "data": node.data if isinstance(node.data, dict) else {}
            })

        for edge in graph.edges or []:
            if edge.node1 is None or edge.node2 is None:
                continue

            edges.append({
                "source": str(edge.node1.index),
                "target": str(edge.node2.index)
            })

        return {
            "nodes": nodes,
            "edges": edges
        }
