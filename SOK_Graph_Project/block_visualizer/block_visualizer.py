import json
from core.service.use_cases.main_view import MainView
from api.graph.api.services.plugin import VisualizationPlugin

class BlockVisualizer(VisualizationPlugin):

    def name(self) -> str:
        return "Block Visualizer"

    def identifier(self) -> str:
        return "block_visualizer"

    def visualize(self, graph):

        main_view = MainView(graph)
        graph_data = main_view.render()

        graph_json = json.dumps(graph_data)

        html = """
        <script src="https://d3js.org/d3.v7.min.js"></script>

        <script>

        const graphData = """ + graph_json + """;

        const width = 900;
        const height = 550;

        const nodeRadius = 80; // približno pola širine rect-a
        let selectedNodeId = null;

        const svg = d3.select("#graph-container")
            .append("svg")
            .attr("width", "100%")
            .attr("height", height);

        const g = svg.append("g");

    const simulation = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.edges)
            .id(d => d.id)
            .distance(200))  // veća udaljenost linkova
        .force("charge", d3.forceManyBody().strength(-3000)) // jača odbojnost
        .force("center", d3.forceCenter(width/2, height/2));

    const link = g.append("g")
        .selectAll("line")
        .data(graphData.edges)
        .enter()
        .append("line")
        .attr("stroke", "#999")
        .attr("stroke-width", 2);

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

        node.each(function(d){

            const group = d3.select(this);

            const lines = [
                "id: " + d.id,
                ...Object.entries(d.data)
                    .map(([k,v]) => k + ": " + v)
            ];

            const lineHeight = 18;
            const padding = 10;

            const rectHeight = lines.length * lineHeight + padding*2;
            const rectWidth = 160;

            group.append("rect")
                .attr("x", -rectWidth/2)
                .attr("y", -rectHeight/2)
                .attr("width", rectWidth)
                .attr("height", rectHeight)
                .attr("rx", 6)
                .attr("fill", "#4CAF50");

            const text = group.append("text")
                .attr("text-anchor", "middle")
                .attr("fill", "white")
                .attr("y", -rectHeight/2 + padding + 10);

            lines.forEach((line,i)=>{
                text.append("tspan")
                    .attr("x",0)
                    .attr("dy", i === 0 ? 0 : lineHeight)
                    .text(line);
            });

            node.on("click", (event, d) => {
                selectedNodeId = d.id;
                notifyBirdView();

                window.dispatchEvent(new CustomEvent("graph-node-selected", {
                    detail: {
                        nodeId: d.id,
                        source: "block-visualizer"
                    }
                }));
            });

    });

    // Update positions on tick
    simulation.on("tick", () => {

        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node.attr("transform", d => "translate(" + d.x + "," + d.y + ")");
        notifyBirdView();
    });

    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
        notifyBirdView();
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
        notifyBirdView();
    }

    const zoom = d3.zoom()
        .scaleExtent([0.07, 4])
        .on("zoom", (event) => g.attr("transform", event.transform));
        notifyBirdView();

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

    function notifyBirdView() {
        window.mainGraphState = {
            nodes: graphData.nodes,
            edges: graphData.edges,
            width: width,
            height: height,
            nodeWidth: nodeRadius * 2,
            nodeHeight: nodeRadius * 2,
            nodeRadius: nodeRadius,
            selectedNodeId: selectedNodeId,
            transform: d3.zoomTransform(svg.node())
        };

        window.dispatchEvent(new CustomEvent("main-view-updated"));
    }

    notifyBirdView();

    </script>
    """

        return html