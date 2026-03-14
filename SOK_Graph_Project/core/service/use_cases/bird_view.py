import json


class BirdView:
    MINI_WIDTH = 240
    MINI_HEIGHT = 180
    PADDING = 12

    def render(self, workspace_id="default-workspace") -> str:
        w = self.MINI_WIDTH
        h = self.MINI_HEIGHT
        pad = self.PADDING
        workspace_id_json = json.dumps(str(workspace_id))

        html = f"""
        <script>
        (function() {{
            const workspaceId = {workspace_id_json};
            const birdContainer = d3.select("#bird-canvas");
            if (birdContainer.empty()) return;

            birdContainer.selectAll("svg").remove();

            const bW = {w};
            const bH = {h};
            const padding = {pad};

            const bSvg = birdContainer
                .append("svg")
                .attr("width", bW)
                .attr("height", bH)
                .style("width", "100%")
                .style("height", "100%")
                .style("background", "#1a1a2e")
                .style("border-radius", "4px")
                .style("border", "1px solid #444");

            const edgeLayer = bSvg.append("g");
            const nodeLayer = bSvg.append("g");

            const viewport = bSvg.append("rect")
                .attr("fill", "rgba(240,165,0,0.10)")
                .attr("stroke", "#f0a500")
                .attr("stroke-width", 1.5)
                .attr("stroke-dasharray", "4,2")
                .style("pointer-events", "none");

            function isFiniteNumber(v) {{
                return Number.isFinite(v);
            }}

            function clamp(value, min, max) {{
                return Math.max(min, Math.min(max, value));
            }}

            function computeBounds(nodes, nodeRadius) {{
                const validNodes = nodes.filter(d => isFiniteNumber(d.x) && isFiniteNumber(d.y));

                if (!validNodes.length) {{
                    return {{
                        minX: 0,
                        maxX: 1,
                        minY: 0,
                        maxY: 1
                    }};
                }}

                return {{
                    minX: d3.min(validNodes, d => d.x) - nodeRadius,
                    maxX: d3.max(validNodes, d => d.x) + nodeRadius,
                    minY: d3.min(validNodes, d => d.y) - nodeRadius,
                    maxY: d3.max(validNodes, d => d.y) + nodeRadius
                }};
            }}

            function renderBirdView() {{
                window.workspaceGraphStates = window.workspaceGraphStates || {{}};
                const main = window.workspaceGraphStates[workspaceId];

                if (!main || !main.nodes || !main.nodes.length) return;

                const nodeRadius = Math.max(main.nodeRadius || 6, 1);
                const bounds = computeBounds(main.nodes, nodeRadius);

                const graphWidth = Math.max(bounds.maxX - bounds.minX, 1);
                const graphHeight = Math.max(bounds.maxY - bounds.minY, 1);

                const scale = Math.min(
                    (bW - 2 * padding) / graphWidth,
                    (bH - 2 * padding) / graphHeight
                );

                const offsetX = (bW - graphWidth * scale) / 2;
                const offsetY = (bH - graphHeight * scale) / 2;

                function mapX(x) {{
                    return offsetX + (x - bounds.minX) * scale;
                }}

                function mapY(y) {{
                    return offsetY + (y - bounds.minY) * scale;
                }}

                const validEdges = (main.edges || []).filter(d =>
                    d.source && d.target &&
                    isFiniteNumber(d.source.x) && isFiniteNumber(d.source.y) &&
                    isFiniteNumber(d.target.x) && isFiniteNumber(d.target.y)
                );

                const edges = edgeLayer.selectAll("line")
                    .data(validEdges, d => `${{d.source.id}}-${{d.target.id}}`);

                edges.enter()
                    .append("line")
                    .merge(edges)
                    .attr("x1", d => mapX(d.source.x))
                    .attr("y1", d => mapY(d.source.y))
                    .attr("x2", d => mapX(d.target.x))
                    .attr("y2", d => mapY(d.target.y))
                    .attr("stroke", "#666")
                    .attr("stroke-width", 1);

                edges.exit().remove();

                const validNodes = (main.nodes || []).filter(d =>
                    isFiniteNumber(d.x) && isFiniteNumber(d.y)
                );

                const nodes = nodeLayer.selectAll("circle")
                    .data(validNodes, d => d.id);

                nodes.enter()
                    .append("circle")
                    .attr("r", 5)
                    .style("cursor", "pointer")
                    .merge(nodes)
                    .attr("cx", d => mapX(d.x))
                    .attr("cy", d => mapY(d.y))
                    .attr("fill", d =>
                        String(d.id) === String(main.selectedNodeId) ? "#4a90e2" : "#4CAF50"
                    )
                    .attr("stroke", d =>
                        String(d.id) === String(main.selectedNodeId) ? "#dcecff" : "#1d1d1d"
                    )
                    .attr("stroke-width", d =>
                        String(d.id) === String(main.selectedNodeId) ? 2 : 1
                    )
                    .on("click", function(event, d) {{
                        event.stopPropagation();

                        window.dispatchEvent(new CustomEvent("graph-node-selected", {{
                            detail: {{
                                workspaceId: workspaceId,
                                nodeId: d.id,
                                source: "bird-view",
                                panTo: true
                            }}
                        }}));
                    }});

                nodes.exit().remove();

                const t = main.transform || {{ x: 0, y: 0, k: 1 }};

                const visibleLeft = (0 - t.x) / t.k;
                const visibleTop = (0 - t.y) / t.k;
                const visibleWidth = main.width / t.k;
                const visibleHeight = main.height / t.k;

                let vx = mapX(visibleLeft);
                let vy = mapY(visibleTop);
                let vw = visibleWidth * scale;
                let vh = visibleHeight * scale;

                vw = Math.max(8, vw);
                vh = Math.max(8, vh);

                vx = clamp(vx, 0, Math.max(0, bW - vw));
                vy = clamp(vy, 0, Math.max(0, bH - vh));

                viewport
                    .attr("x", vx)
                    .attr("y", vy)
                    .attr("width", Math.min(vw, bW))
                    .attr("height", Math.min(vh, bH));
            }}

            window.addEventListener("main-view-updated", function(event) {{
                const detail = event.detail || {{}};
                if (detail.workspaceId !== workspaceId) return;
                renderBirdView();
            }});

            window.addEventListener("graph-node-selected", function(event) {{
                const detail = event.detail || {{}};
                if (detail.workspaceId !== workspaceId) return;
                renderBirdView();
            }});

            renderBirdView();
        }})();
        </script>
        """
        return html