import json

from core.service.use_cases.main_view import MainView
from api.graph.api.services.plugin import VisualizationPlugin
from api.graph.api.model.graph import Graph


class BlockVisualizer(VisualizationPlugin):

    def name(self) -> str:
        return "Block Visualizer"

    def identifier(self) -> str:
        return "block_visualizer"

    def visualize(self, graph: Graph, **kwargs) -> str:
        workspace_id = kwargs.get("workspace_id", "default-workspace")
        workspace_id_json = json.dumps(str(workspace_id))

        main_view = MainView(graph)
        graph_data = main_view.render()
        graph_json = json.dumps(graph_data)

        container_id = kwargs.get("container_id", f"block-visualizer-{workspace_id}")

        html = f"""
        <style>
            #{container_id} rect.selected {{
                fill: #FF5722;
                stroke: #1f5fa8;
                stroke-width: 3px;
            }}
        </style>

        <div id="{container_id}"></div>

        <script src="https://d3js.org/d3.v7.min.js"></script>
        <script>
        (function() {{
            const workspaceId = {workspace_id_json};
            const graphData = {graph_json};
            const container = d3.select("#{container_id}");

            container.selectAll("*").remove();

            window.workspaceGraphStates = window.workspaceGraphStates || {{}};

            const width = 900;
            const height = 550;
            const nodeRadius = 80;
            let selectedNodeId = null;

            const svg = container
                .append("svg")
                .attr("width", "100%")
                .attr("height", height);

            const defs = svg.append("defs");

            defs.append("marker")
                .attr("id", `block-arrowhead-${{workspaceId}}`)
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 90)
                .attr("refY", 0)
                .attr("markerWidth", 7)
                .attr("markerHeight", 7)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("fill", "#999");

            const g = svg.append("g");

            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.edges)
                    .id(d => d.id)
                    .distance(200))
                .force("charge", d3.forceManyBody().strength(-3000))
                .force("center", d3.forceCenter(width / 2, height / 2));

            const link = g.append("g")
                .selectAll("line")
                .data(graphData.edges)
                .enter()
                .append("line")
                .attr("stroke", "#999")
                .attr("stroke-width", 2)
                .attr("marker-end", graphData.directed ? `url(#block-arrowhead-${{workspaceId}})` : null);

            const node = g.append("g")
                .selectAll("g")
                .data(graphData.nodes)
                .enter()
                .append("g")
                .call(
                    d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended)
                );

            node.each(function(d) {{
                const group = d3.select(this);

                const lines = [
                    "id: " + d.id,
                    ...Object.entries(d.data || {{}}).map(([k, v]) => k + ": " + v)
                ];

                const lineHeight = 18;
                const padding = 10;
                const rectHeight = lines.length * lineHeight + padding * 2;
                const rectWidth = 160;

                group.append("rect")
                    .attr("x", -rectWidth / 2)
                    .attr("y", -rectHeight / 2)
                    .attr("width", rectWidth)
                    .attr("height", rectHeight)
                    .attr("rx", 6)
                    .attr("fill", "#4CAF50");

                const text = group.append("text")
                    .attr("text-anchor", "middle")
                    .attr("fill", "white")
                    .attr("y", -rectHeight / 2 + padding + 10);

                lines.forEach((line, i) => {{
                    text.append("tspan")
                        .attr("x", 0)
                        .attr("dy", i === 0 ? 0 : lineHeight)
                        .text(line);
                }});
            }});

            function updateSelectedNode() {{
                node.selectAll("rect")
                    .classed("selected", n => String(n.id) === String(selectedNodeId));
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

            node.on("click", (event, d) => {{
                selectedNodeId = d.id;
                updateSelectedNode();
                notifyBirdView();

                window.dispatchEvent(new CustomEvent("graph-node-selected", {{
                    detail: {{
                        workspaceId: workspaceId,
                        nodeId: d.id,
                        source: "{container_id}"
                    }}
                }}));
            }});

            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node.attr("transform", d => "translate(" + d.x + "," + d.y + ")");
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

            const zoom = d3.zoom()
                .scaleExtent([0.07, 4])
                .on("zoom", (event) => {{
                    g.attr("transform", event.transform);
                    notifyBirdView();
                }});

            svg.call(zoom);

            function notifyBirdView() {{
                window.workspaceGraphStates[workspaceId] = {{
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

                window.dispatchEvent(new CustomEvent("main-view-updated", {{
                    detail: {{
                        workspaceId: workspaceId
                    }}
                }}));
            }}

            window.addEventListener("graph-node-selected", function(event) {{
                const detail = event.detail || {{}};
                if (detail.workspaceId !== workspaceId) return;
                if (detail.nodeId == null) return;
                if (detail.source === "{container_id}") return;

                selectedNodeId = detail.nodeId;
                updateSelectedNode();

                if (detail.panTo) {{
                    focusNode(detail.nodeId);
                }}

                notifyBirdView();
            }});

            notifyBirdView();
        }})();
        </script>
        """

        return html