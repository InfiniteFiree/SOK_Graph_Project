class BirdView:
    MINI_WIDTH = 240
    MINI_HEIGHT = 180
    PADDING = 12

    def render(self, graph: dict) -> str:
        w = self.MINI_WIDTH
        h = self.MINI_HEIGHT
        pad = self.PADDING

        html = f"""
        <script>
        (function() {{
            const birdContainer = d3.select("#bird-canvas");
            birdContainer.selectAll("svg").remove();

            const bW = {w};
            const bH = {h};
            const padding = {pad};

            const bSvg = birdContainer
                .append("svg")
                .attr("width", bW)
                .attr("height", bH)
                .style("background", "#1a1a2e")
                .style("border-radius", "4px")
                .style("border", "1px solid #444");

            const edgeLayer = bSvg.append("g");
            const nodeLayer = bSvg.append("g");

            const viewport = bSvg.append("rect")
                .attr("fill", "none")
                .attr("stroke", "#f0a500")
                .attr("stroke-width", 1.5)
                .attr("stroke-dasharray", "4,2");

            function computeBounds(nodes, nodeWidth, nodeHeight) {{
                return {{
                    minX: d3.min(nodes, d => d.x) - nodeWidth / 2,
                    maxX: d3.max(nodes, d => d.x) + nodeWidth / 2,
                    minY: d3.min(nodes, d => d.y) - nodeHeight / 2,
                    maxY: d3.max(nodes, d => d.y) + nodeHeight / 2
                }};
            }}

            function renderBirdView() {{
                const main = window.mainGraphState;
                if (!main || !main.nodes || !main.nodes.length) return;

                const bounds = computeBounds(main.nodes, main.nodeWidth, main.nodeHeight);
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

                const edges = edgeLayer.selectAll("line")
                    .data(main.edges);

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

                const nodes = nodeLayer.selectAll("circle")
                    .data(main.nodes);

                nodes.enter()
                    .append("circle")
                    .attr("r", 4)
                    .merge(nodes)
                    .attr("cx", d => mapX(d.x))
                    .attr("cy", d => mapY(d.y))
                    .attr("fill", "#4CAF50");

                nodes.exit().remove();

                const t = main.transform;

                const visibleLeft = (0 - t.x) / t.k;
                const visibleTop = (0 - t.y) / t.k;
                const visibleWidth = main.width / t.k;
                const visibleHeight = main.height / t.k;

                viewport
                    .attr("x", mapX(visibleLeft))
                    .attr("y", mapY(visibleTop))
                    .attr("width", visibleWidth * scale)
                    .attr("height", visibleHeight * scale);
            }}

            window.addEventListener("main-view-updated", renderBirdView);
            renderBirdView();
        }})();
        console.log("Bird view loaded");
        </script>
        """
        return html