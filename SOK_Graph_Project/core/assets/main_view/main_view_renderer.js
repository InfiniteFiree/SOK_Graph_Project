(function () {
    function getCurrentVisualizationModel() {
        if (window.currentVisualizationModel !== undefined && window.currentVisualizationModel !== null) {
            return window.currentVisualizationModel;
        }

        const modelTag = document.getElementById("current-visualization-model");
        if (!modelTag) return null;

        try {
            return JSON.parse(modelTag.textContent);
        } catch (error) {
            console.error("Failed to parse visualization model JSON", error);
            return null;
        }
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function buildBase(model) {
        const graphContainer = document.getElementById("graph-container");
        if (!graphContainer) return null;

        graphContainer.innerHTML = "";

        const workspaceId = String(model.workspace_id || "default-workspace");
        const graphData = model.graph || { nodes: [], edges: [], directed: false, cyclic: false };
        const options = model.options || {};

        const width = options.width || 900;
        const height = options.height || 550;
        const linkDistance = options.link_distance || 140;
        const chargeStrength = options.charge_strength || -500;
        const containerId = options.container_id || `main-view-${workspaceId}`;
        const arrowRefX = options.arrow_ref_x || 40;

        const wrapper = document.createElement("div");
        wrapper.id = containerId;
        wrapper.className = "main-view-wrapper";

        const canvas = document.createElement("div");
        canvas.className = "main-view-canvas";
        canvas.style.height = `${height}px`;

        wrapper.appendChild(canvas);
        graphContainer.appendChild(wrapper);

        window.workspaceGraphStates = window.workspaceGraphStates || {};

        const svg = d3.select(canvas)
            .append("svg")
            .attr("width", canvas.clientWidth || width)
            .attr("height", height)
            .attr("viewBox", `0 0 ${canvas.clientWidth || width} ${height}`)
            .attr("preserveAspectRatio", "xMidYMid meet");

        const defs = svg.append("defs");

        defs.append("marker")
            .attr("id", `arrowhead-${workspaceId}`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", arrowRefX)
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
            .on("zoom", function (event) {
                graphLayer.attr("transform", event.transform);
                notifyBirdView();
            });

        svg.call(zoom);

        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.edges)
                .id(d => d.id)
                .distance(linkDistance))
            .force("charge", d3.forceManyBody().strength(chargeStrength))
            .force("center", d3.forceCenter((canvas.clientWidth || width) / 2, height / 2));

        const links = graphLayer.append("g")
            .selectAll("line")
            .data(graphData.edges)
            .enter()
            .append("line")
            .attr("class", "link")
            .attr("marker-end", graphData.directed ? `url(#arrowhead-${workspaceId})` : null);

        let selectedNodeId = null;

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

        function focusNode(nodeId) {
            const targetNode = graphData.nodes.find(n => String(n.id) === String(nodeId));
            if (!targetNode) return;
            if (!Number.isFinite(targetNode.x) || !Number.isFinite(targetNode.y)) return;

            const currentTransform = d3.zoomTransform(svg.node());
            const currentScale = currentTransform.k || 1;

            const widthNow = canvas.clientWidth || width;
            const targetX = widthNow / 2 - targetNode.x * currentScale;
            const targetY = height / 2 - targetNode.y * currentScale;

            const newTransform = d3.zoomIdentity
                .translate(targetX, targetY)
                .scale(currentScale);

            svg.transition()
                .duration(400)
                .call(zoom.transform, newTransform);
        }

        function findNodeById(nodeId) {
            return graphData.nodes.find(n => String(n.id) === String(nodeId)) || null;
        }

        function notifyBirdView(nodeSizeInfo = { nodeWidth: 56, nodeHeight: 56, nodeRadius: 28 }) {
            window.workspaceGraphStates[workspaceId] = {
                nodes: graphData.nodes,
                edges: graphData.edges,
                width: canvas.clientWidth || width,
                height: height,
                nodeWidth: nodeSizeInfo.nodeWidth,
                nodeHeight: nodeSizeInfo.nodeHeight,
                nodeRadius: nodeSizeInfo.nodeRadius,
                selectedNodeId: selectedNodeId,
                transform: d3.zoomTransform(svg.node())
            };

            window.dispatchEvent(new CustomEvent("main-view-updated", {
                detail: {
                    workspaceId: workspaceId
                }
            }));
        }

        return {
            workspaceId,
            graphData,
            options,
            width: canvas.clientWidth || width,
            height,
            wrapper,
            canvas,
            svg,
            graphLayer,
            simulation,
            links,
            zoom,
            dragstarted,
            dragged,
            dragended,
            focusNode,
            findNodeById,
            notifyBirdView,
            get selectedNodeId() { return selectedNodeId; },
            set selectedNodeId(value) { selectedNodeId = value; }
        };
    }

    function renderSimpleVisualizer(model) {
        const nodeRadius = (model.options && model.options.node_radius) || 28;
        const env = buildBase({
            ...model,
            options: {
                ...(model.options || {}),
                arrow_ref_x: nodeRadius + 10
            }
        });
        if (!env) return;

        const { wrapper, graphLayer, graphData, simulation, links, dragstarted, dragged, dragended, workspaceId, focusNode, findNodeById, notifyBirdView } = env;

        const overlay = document.createElement("div");
        overlay.className = "simple-visualizer-overlay";
        overlay.style.display = "none";

        const modal = document.createElement("div");
        modal.className = "simple-visualizer-modal";
        modal.style.display = "none";
        modal.innerHTML = `
            <div class="simple-visualizer-modal-header">
                <span>Node Details</span>
                <button type="button" class="simple-visualizer-close-btn">&times;</button>
            </div>
            <div class="simple-visualizer-modal-body"></div>
        `;

        wrapper.appendChild(overlay);
        wrapper.appendChild(modal);

        const closeBtn = modal.querySelector(".simple-visualizer-close-btn");
        const modalBody = modal.querySelector(".simple-visualizer-modal-body");

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
            .on("click", function (event, d) {
                event.stopPropagation();
                selectNode(d.id);
                showNodeDetails(d);
                notifyBirdView({ nodeWidth: nodeRadius * 2, nodeHeight: nodeRadius * 2, nodeRadius: nodeRadius });

                window.dispatchEvent(new CustomEvent("graph-node-selected", {
                    detail: {
                        workspaceId: workspaceId,
                        nodeId: d.id,
                        source: wrapper.id
                    }
                }));
            });

        nodes.append("text")
            .attr("class", "node-label")
            .text(d => `id=${d.id}`);

        simulation
            .force("collision", d3.forceCollide().radius(nodeRadius + 8))
            .on("tick", () => {
                links
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                nodes.attr("transform", d => `translate(${d.x}, ${d.y})`);
                notifyBirdView({ nodeWidth: nodeRadius * 2, nodeHeight: nodeRadius * 2, nodeRadius: nodeRadius });
            });

        function selectNode(nodeId) {
            env.selectedNodeId = String(nodeId);

            nodes.each(function (d) {
                const circle = this.querySelector(".node-circle");
                if (!circle) return;

                if (String(d.id) === env.selectedNodeId) {
                    circle.classList.add("selected");
                } else {
                    circle.classList.remove("selected");
                }
            });
        }

        function showNodeDetails(nodeData) {
            const rows = Object.entries(nodeData.data || {})
                .map(([key, value]) => `
                    <tr>
                        <td class="simple-visualizer-detail-key">${escapeHtml(String(key))}</td>
                        <td>${escapeHtml(String(value))}</td>
                    </tr>
                `)
                .join("");

            modalBody.innerHTML = `
                <table class="simple-visualizer-detail-table">
                    <tr>
                        <td class="simple-visualizer-detail-key">id</td>
                        <td>${escapeHtml(String(nodeData.id))}</td>
                    </tr>
                    ${rows}
                </table>
            `;

            overlay.style.display = "block";
            modal.style.display = "block";
        }

        function hideModal() {
            overlay.style.display = "none";
            modal.style.display = "none";
        }

        closeBtn.addEventListener("click", hideModal);
        overlay.addEventListener("click", hideModal);

        env.svg.on("click", function (event) {
            if (event.target === env.svg.node()) {
                hideModal();
            }
        });

        window.addEventListener("graph-node-selected", function (event) {
            const detail = event.detail || {};
            if (detail.workspaceId !== workspaceId) return;
            if (detail.nodeId == null) return;
            if (detail.source === wrapper.id) return;

            selectNode(detail.nodeId);

            if (detail.panTo) {
                focusNode(detail.nodeId);
            }

            const selectedNode = findNodeById(detail.nodeId);
            if (selectedNode && detail.source === "tree-view") {
                showNodeDetails(selectedNode);
            }

            notifyBirdView({ nodeWidth: nodeRadius * 2, nodeHeight: nodeRadius * 2, nodeRadius: nodeRadius });
        });

        notifyBirdView({ nodeWidth: nodeRadius * 2, nodeHeight: nodeRadius * 2, nodeRadius: nodeRadius });
    }

    function renderBlockVisualizer(model) {
        const nodeRadius = (model.options && model.options.node_radius) || 80;
        const env = buildBase({
            ...model,
            options: {
                ...(model.options || {}),
                arrow_ref_x: 90
            }
        });
        if (!env) return;

        const { wrapper, graphLayer, graphData, simulation, links, dragstarted, dragged, dragended, workspaceId, focusNode, notifyBirdView } = env;

        const nodes = graphLayer.append("g")
            .selectAll("g")
            .data(graphData.nodes)
            .enter()
            .append("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        nodes.each(function (d) {
            const group = d3.select(this);

            const lines = [
                "id: " + d.id,
                ...Object.entries(d.data || {}).map(([k, v]) => k + ": " + v)
            ];

            const lineHeight = 18;
            const padding = 10;
            const rectHeight = lines.length * lineHeight + padding * 2;
            const rectWidth = 160;

            group.append("rect")
                .attr("class", "block-node-rect")
                .attr("x", -rectWidth / 2)
                .attr("y", -rectHeight / 2)
                .attr("width", rectWidth)
                .attr("height", rectHeight)
                .attr("rx", 6);

            const text = group.append("text")
                .attr("class", "block-node-text")
                .attr("y", -rectHeight / 2 + padding + 10);

            lines.forEach((line, i) => {
                text.append("tspan")
                    .attr("x", 0)
                    .attr("dy", i === 0 ? 0 : lineHeight)
                    .text(line);
            });
        });

        function updateSelectedNode() {
            nodes.selectAll("rect")
                .classed("selected", n => String(n.id) === String(env.selectedNodeId));
        }

        nodes.on("click", (event, d) => {
            env.selectedNodeId = d.id;
            updateSelectedNode();
            notifyBirdView({ nodeWidth: nodeRadius * 2, nodeHeight: nodeRadius * 2, nodeRadius: nodeRadius });

            window.dispatchEvent(new CustomEvent("graph-node-selected", {
                detail: {
                    workspaceId: workspaceId,
                    nodeId: d.id,
                    source: wrapper.id
                }
            }));
        });

        simulation.on("tick", () => {
            links
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            nodes.attr("transform", d => "translate(" + d.x + "," + d.y + ")");
            notifyBirdView({ nodeWidth: nodeRadius * 2, nodeHeight: nodeRadius * 2, nodeRadius: nodeRadius });
        });

        window.addEventListener("graph-node-selected", function (event) {
            const detail = event.detail || {};
            if (detail.workspaceId !== workspaceId) return;
            if (detail.nodeId == null) return;
            if (detail.source === wrapper.id) return;

            env.selectedNodeId = detail.nodeId;
            updateSelectedNode();

            if (detail.panTo) {
                focusNode(detail.nodeId);
            }

            notifyBirdView({ nodeWidth: nodeRadius * 2, nodeHeight: nodeRadius * 2, nodeRadius: nodeRadius });
        });

        notifyBirdView({ nodeWidth: nodeRadius * 2, nodeHeight: nodeRadius * 2, nodeRadius: nodeRadius });
    }

    window.renderCurrentVisualization = function () {
        const model = getCurrentVisualizationModel();
        if (!model) return;

        if (model.plugin_id === "simple_visualizer") {
            renderSimpleVisualizer(model);
        } else if (model.plugin_id === "block_visualizer") {
            renderBlockVisualizer(model);
        }
    };

    window.renderCurrentVisualization();
})();