import json
from core.service.use_cases.main_view import MainView


class BlockVisualizer:

    def visualize(self, graph):

        main_view = MainView(graph)
        graph_data = main_view.render()

        graph_json = json.dumps(graph_data)

        html = """
        <script src="https://d3js.org/d3.v7.min.js"></script>

        <script>

        const graphData = """ + graph_json + """;

        const width = 900;
        const height = 500;

        const svg = d3.select("#graph-container")
            .append("svg")
            .attr("width", "100%")
            .attr("height", height);

        const g = svg.append("g");

    const simulation = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.edges)
            .id(d => d.id)
            .distance(150))
        .force("charge", d3.forceManyBody().strength(-400))
        .force("center", d3.forceCenter(width/2, height/2));

    const link = g.append("g")
        .selectAll("line")
        .data(graphData.edges)
        .enter()
        .append("line")
        .attr("stroke", "#999")
        .attr("stroke-width", 2);


    // g element per node
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


    // Circle for each node
    node.append("circle")
        .attr("r", 30)
        .attr("fill", "#4CAF50");


    // Text inside each circle
    node.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", 5)
        .attr("fill", "white")
        .text(d => d.data.name);


    // Click event to show node details
    node.on("click", (event, d) => {

        const details = Object.entries(d.data)
            .map(([key, value]) => key + ": " + value)
            .join("\\n");

        alert("Node ID: " + d.id + "\\n" + details);
    });


    // Update positions on tick
    simulation.on("tick", () => {

        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node.attr("transform", d => "translate(" + d.x + "," + d.y + ")");
    });


    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }


    const zoom = d3.zoom()
        .scaleExtent([0.5, 5])
        .on("zoom", (event) => g.attr("transform", event.transform));

    svg.call(zoom);


    node.call(
        d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
    );


    // Kreiraj div tooltip u HTML-u
    const tooltip = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("background", "#333")
    .style("color", "#fff")
    .style("padding", "5px 10px")
    .style("border-radius", "4px")
    .style("pointer-events", "none")
    .style("opacity", 0);

    node.on("mouseover", (event, d) => {
    const details = Object.entries(d.data)
        .map(([key, value]) => key + ": " + value)
        .join("<br>");
    tooltip.html("ID: " + d.id + "<br>" + details)
        .style("opacity", 1)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY + 10) + "px");
    })

    .on("mousemove", (event) => {
    tooltip.style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY + 10) + "px");
    })

    .on("mouseout", () => {
    tooltip.style("opacity", 0);
    });

    </script>
    """

        return html