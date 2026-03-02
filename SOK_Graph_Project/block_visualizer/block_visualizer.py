import json

class BlockVisualizer:

    def visualize(self, graph):
        graph_json = json.dumps(graph)

        html = f"""
        <script>
        const graphData = {graph_json};

        const width = 800;
        const height = 600;

        const svg = d3.select("#graph-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .selectAll("line")
            .data(graphData.edges)
            .enter()
            .append("line")
            .attr("stroke", "#999");

        const node = svg.append("g")
            .selectAll("g")
            .data(graphData.nodes)
            .enter()
            .append("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("rect")
            .attr("width", 120)
            .attr("height", 60)
            .attr("fill", "#4CAF50")
            .attr("rx", 5);

        node.append("text")
            .attr("x", 10)
            .attr("y", 20)
            .text(d => d.id);

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("transform", d => "translate(" + d.x + "," + d.y + ")");
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        </script>
        """

        return html