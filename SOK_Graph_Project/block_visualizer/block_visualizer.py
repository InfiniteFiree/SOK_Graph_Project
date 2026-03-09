import json

class BlockVisualizer:

    def visualize(self, graph):
        graph_json = json.dumps(graph)

        html = f"""
        <script>
        (function() {{
            const graphData = {graph_json};

            d3.select("#graph-container").selectAll("svg").remove();

            const width = 800;
            const height = 600;
            const nodeWidth = 120;
            const nodeHeight = 60;

            const svg = d3.select("#graph-container")
                .append("svg")
                .attr("width", width)
                .attr("height", height)
                .style("border", "1px solid #ccc");

            const graphLayer = svg.append("g");

            const zoom = d3.zoom()
                .scaleExtent([0.2, 4])
                .on("zoom", function(event) {{
                    graphLayer.attr("transform", event.transform);
                    notifyBirdView();
                }});

            svg.call(zoom);

            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(150))
                .force("charge", d3.forceManyBody().strength(-400))
                .force("center", d3.forceCenter(width / 2, height / 2));

            const link = graphLayer.append("g")
                .selectAll("line")
                .data(graphData.edges)
                .enter()
                .append("line")
                .attr("stroke", "#999");

            const node = graphLayer.append("g")
                .selectAll("g")
                .data(graphData.nodes)
                .enter()
                .append("g")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            node.append("rect")
                .attr("x", -nodeWidth / 2)
                .attr("y", -nodeHeight / 2)
                .attr("width", nodeWidth)
                .attr("height", nodeHeight)
                .attr("fill", "#4CAF50")
                .attr("rx", 5);

            node.append("text")
                .attr("text-anchor", "middle")
                .attr("y", 5)
                .attr("fill", "white")
                .text(d => d.id);

            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node
                    .attr("transform", d => "translate(" + d.x + "," + d.y + ")");

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

            function notifyBirdView() {{
                window.mainGraphState = {{
                    nodes: graphData.nodes,
                    edges: graphData.edges,
                    width: width,
                    height: height,
                    nodeWidth: nodeWidth,
                    nodeHeight: nodeHeight,
                    transform: d3.zoomTransform(svg.node())
                }};

                window.dispatchEvent(new CustomEvent("main-view-updated"));
            }}
        }})();
        </script>
        """

        return html