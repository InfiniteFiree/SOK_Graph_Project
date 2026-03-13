import html
import json
from collections import defaultdict, deque


class TreeView:
    """
    Lazy, workspace-aware tree view.

    Features:
    - supports multiple disconnected graph components
    - renders one root per disconnected graph/component
    - lazily loads children only when a node is opened
    - allows repeated graph-node appearances in the tree
    - children are derived from outgoing edges (node1 -> node2)
    - for undirected graphs, reverse adjacency is also included
    - reacts to node selection from the main view
    - dispatches selection back to the main view
    """

    def __init__(self, graph=None):
        self.graph = graph

    def render(self, workspace_id="default-workspace"):
        if self.graph is None or not getattr(self.graph, "nodes", None):
            return self._fallback_placeholder()

        node_map = self._build_node_map()
        outgoing_adjacency = self._build_outgoing_adjacency()
        undirected_adjacency = self._build_undirected_adjacency()
        root_ids = self._choose_root_ids(outgoing_adjacency, undirected_adjacency)

        if not root_ids:
            return self._fallback_placeholder()

        return self._render_lazy_forest(
            node_map=node_map,
            adjacency=outgoing_adjacency,
            undirected_adjacency=undirected_adjacency,
            root_ids=root_ids,
            workspace_id=workspace_id
        )

    def _build_node_map(self):
        node_map = {}
        for node in self.graph.nodes:
            node_id = str(node.index)
            node_map[node_id] = {
                "id": node_id,
                "data": node.data if isinstance(node.data, dict) else {}
            }
        return node_map

    def _build_outgoing_adjacency(self):
        adjacency = {str(node.index): [] for node in self.graph.nodes}

        for edge in getattr(self.graph, "edges", []) or []:
            if edge.node1 is None or edge.node2 is None:
                continue

            source_id = str(edge.node1.index)
            target_id = str(edge.node2.index)

            if source_id in adjacency:
                adjacency[source_id].append(target_id)

            if not getattr(self.graph, "directed", True):
                if target_id in adjacency:
                    adjacency[target_id].append(source_id)

        for node_id in adjacency:
            adjacency[node_id] = sorted(adjacency[node_id], key=self._sort_key)

        return adjacency

    def _build_undirected_adjacency(self):
        adjacency = defaultdict(set)

        for node in self.graph.nodes:
            adjacency[str(node.index)] = set()

        for edge in getattr(self.graph, "edges", []) or []:
            if edge.node1 is None or edge.node2 is None:
                continue

            source_id = str(edge.node1.index)
            target_id = str(edge.node2.index)

            adjacency[source_id].add(target_id)
            adjacency[target_id].add(source_id)

        return {
            node_id: sorted(list(neighbors), key=self._sort_key)
            for node_id, neighbors in adjacency.items()
        }

    def _choose_root_ids(self, outgoing_adjacency, undirected_adjacency):
        nodes = self.graph.nodes or []
        if not nodes:
            return []

        node_ids = [str(node.index) for node in nodes]

        # Build connected components using undirected adjacency
        components = []
        visited = set()

        for node_id in sorted(node_ids, key=self._sort_key):
            if node_id in visited:
                continue

            component = []
            queue = deque([node_id])
            visited.add(node_id)

            while queue:
                current = queue.popleft()
                component.append(current)

                for neighbor in undirected_adjacency.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            components.append(sorted(component, key=self._sort_key))

        # For each component, choose at least one root
        indegree = {node_id: 0 for node_id in node_ids}
        for source_id, targets in outgoing_adjacency.items():
            for target_id in targets:
                if target_id in indegree:
                    indegree[target_id] += 1

        root_ids = []

        for component in components:
            zero_indegree = [node_id for node_id in component if indegree[node_id] == 0]

            if zero_indegree:
                root_ids.append(sorted(zero_indegree, key=self._sort_key)[0])
            else:
                # cyclic / fully strongly connected component fallback
                root_ids.append(sorted(component, key=self._sort_key)[0])

        return sorted(root_ids, key=self._sort_key)

    def _sort_key(self, value):
        try:
            return (0, int(value))
        except Exception:
            return (1, str(value))

    def _render_lazy_forest(self, node_map, adjacency, undirected_adjacency, root_ids, workspace_id):
        node_map_json = json.dumps(node_map)
        adjacency_json = json.dumps(adjacency)
        workspace_id_json = json.dumps(str(workspace_id))
        root_ids_json = json.dumps(root_ids)

        root_items_html = "".join(
            f"""
            <li class="tree-node-item open selected-root"
                data-instance-id="root-{html.escape(root_id)}"
                data-graph-node-id="{html.escape(root_id)}"
                data-parent-instance-id="">
                <div class="tree-node-header">
                    <button type="button" class="tree-toggle" data-role="toggle">-</button>
                    <span class="tree-node-title">id: {html.escape(root_id)}</span>
                </div>
                <div class="tree-node-body"></div>
            </li>
            """
            for root_id in root_ids
        )

        return f"""
        <div id="tree-view-root" class="tree-view-root">
            <ul class="tree-root-list">
                {root_items_html}
            </ul>
        </div>

        <style>
            .tree-view-root {{
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #222;
            }}

            .tree-root-list,
            .tree-children-list,
            .tree-data-list {{
                list-style: none;
                margin: 0;
                padding: 0;
            }}

            .tree-node-item {{
                margin: 4px 0;
            }}

            .tree-node-header {{
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 4px 6px;
                border-radius: 6px;
                cursor: pointer;
                user-select: none;
            }}

            .tree-node-header:hover {{
                background: #f4f8ff;
            }}

            .tree-node-item.selected > .tree-node-header {{
                background: #e6f0ff;
                outline: 1px solid #4a90e2;
            }}

            .tree-node-item.selected-root > .tree-node-header {{
                background: #f8fbff;
                border: 1px solid #d9e8ff;
            }}

            .tree-toggle {{
                width: 20px;
                height: 20px;
                border: none;
                background: transparent;
                font-weight: bold;
                font-size: 14px;
                line-height: 1;
                cursor: pointer;
                color: #1f5fa8;
                padding: 0;
            }}

            .tree-node-title {{
                font-weight: 600;
                color: #222;
            }}

            .tree-node-body {{
                display: none;
                margin-left: 26px;
                padding: 2px 0 4px 0;
            }}

            .tree-node-item.open > .tree-node-body {{
                display: block;
            }}

            .tree-section-label {{
                font-weight: 600;
                color: #555;
                margin: 4px 0 2px 0;
            }}

            .tree-data-list {{
                margin-left: 14px;
            }}

            .tree-data-item {{
                padding: 2px 0;
            }}

            .tree-data-key {{
                font-weight: 600;
            }}

            .tree-children-list {{
                margin-left: 14px;
            }}
        </style>

        <script>
        (function() {{
            const workspaceId = {workspace_id_json};
            const nodeMap = {node_map_json};
            const adjacency = {adjacency_json};
            const rootIds = {root_ids_json};

            const treeRoot = document.getElementById("tree-view-root");
            if (!treeRoot) return;

            let instanceCounter = 0;

            function nextInstanceId() {{
                instanceCounter += 1;
                return "instance-" + instanceCounter;
            }}

            function sortIds(ids) {{
                return [...ids].sort((a, b) => {{
                    const na = Number(a), nb = Number(b);
                    const aNum = Number.isFinite(na) && String(na) === String(a);
                    const bNum = Number.isFinite(nb) && String(nb) === String(b);

                    if (aNum && bNum) return na - nb;
                    if (aNum) return -1;
                    if (bNum) return 1;
                    return String(a).localeCompare(String(b));
                }});
            }}

            function findInstanceById(instanceId) {{
                return treeRoot.querySelector(`.tree-node-item[data-instance-id="${{CSS.escape(String(instanceId))}}"]`);
            }}

            function getAllInstancesForGraphNode(graphNodeId) {{
                return Array.from(treeRoot.querySelectorAll(`.tree-node-item[data-graph-node-id="${{CSS.escape(String(graphNodeId))}}"]`));
            }}

            function clearSelection() {{
                treeRoot.querySelectorAll(".tree-node-item.selected").forEach(el => {{
                    el.classList.remove("selected");
                }});
            }}

            function highlightInstance(instanceEl) {{
                if (!instanceEl) return;
                clearSelection();
                instanceEl.classList.add("selected");
                instanceEl.scrollIntoView({{
                    behavior: "smooth",
                    block: "nearest"
                }});
            }}

            function setOpen(item, shouldOpen) {{
                if (!item) return;
                item.classList.toggle("open", shouldOpen);
                const toggle = item.querySelector(':scope > .tree-node-header [data-role="toggle"]');
                if (toggle) {{
                    toggle.textContent = shouldOpen ? "-" : "+";
                }}
            }}

            function buildDataHtml(graphNodeId) {{
                const node = nodeMap[graphNodeId];
                if (!node) return "";

                const entries = Object.entries(node.data || {{}});
                if (!entries.length) return "";

                const rows = entries.map(([key, value]) => `
                    <li class="tree-data-item">
                        <span class="tree-data-key">${{escapeHtml(String(key))}}</span>:
                        <span class="tree-data-value">${{escapeHtml(String(value))}}</span>
                    </li>
                `).join("");

                return `
                    <div class="tree-section-label">data:</div>
                    <ul class="tree-data-list">${{rows}}</ul>
                `;
            }}

            function buildChildrenShellHtml(parentGraphNodeId, parentInstanceId) {{
                const children = sortIds(adjacency[parentGraphNodeId] || []);
                if (!children.length) return "";

                const items = children.map(childId => {{
                    const instanceId = nextInstanceId();
                    return `
                        <li class="tree-node-item"
                            data-instance-id="${{escapeHtml(instanceId)}}"
                            data-graph-node-id="${{escapeHtml(String(childId))}}"
                            data-parent-instance-id="${{escapeHtml(String(parentInstanceId))}}">
                            <div class="tree-node-header">
                                <button type="button" class="tree-toggle" data-role="toggle">+</button>
                                <span class="tree-node-title">id: ${{escapeHtml(String(childId))}}</span>
                            </div>
                            <div class="tree-node-body"></div>
                        </li>
                    `;
                }}).join("");

                return `
                    <div class="tree-section-label">children:</div>
                    <ul class="tree-children-list">${{items}}</ul>
                `;
            }}

            function ensureNodeContentBuilt(item) {{
                if (!item) return;
                if (item.dataset.built === "true") return;

                const graphNodeId = item.dataset.graphNodeId;
                const instanceId = item.dataset.instanceId;
                const body = item.querySelector(':scope > .tree-node-body');
                if (!body) return;

                body.innerHTML = buildDataHtml(graphNodeId) + buildChildrenShellHtml(graphNodeId, instanceId);
                item.dataset.built = "true";

                attachHandlersWithin(item);
            }}

            function openNode(item) {{
                if (!item) return;
                ensureNodeContentBuilt(item);
                setOpen(item, true);
            }}

            function closeNode(item) {{
                if (!item) return;
                setOpen(item, false);
            }}

            function attachHandlersWithin(scope) {{
                const items = scope.querySelectorAll('.tree-node-item');

                items.forEach(item => {{
                    if (item.dataset.handlersAttached === "true") return;
                    item.dataset.handlersAttached = "true";

                    const header = item.querySelector(':scope > .tree-node-header');
                    const toggle = item.querySelector(':scope > .tree-node-header [data-role="toggle"]');

                    if (toggle) {{
                        toggle.addEventListener("click", function(event) {{
                            event.stopPropagation();

                            const graphNodeId = item.dataset.graphNodeId;
                            const isOpen = item.classList.contains("open");

                            if (isOpen) {{
                                closeNode(item);
                            }} else {{
                                openNode(item);
                                selectAndBroadcast(graphNodeId, item);
                            }}
                        }});
                    }}

                    if (header) {{
                        header.addEventListener("click", function() {{
                            const graphNodeId = item.dataset.graphNodeId;
                            openNode(item);
                            selectAndBroadcast(graphNodeId, item);
                        }});
                    }}
                }});
            }}

            function selectAndBroadcast(graphNodeId, item) {{
                highlightInstance(item);

                window.dispatchEvent(new CustomEvent("graph-node-selected", {{
                    detail: {{
                        workspaceId: workspaceId,
                        nodeId: String(graphNodeId),
                        source: "tree-view",
                        panTo: true
                    }}
                }}));
            }}

            function bfsPathFromRoot(rootId, targetId) {{
                rootId = String(rootId);
                targetId = String(targetId);

                if (rootId === targetId) return [rootId];

                const queue = [[rootId]];
                const visited = new Set([rootId]);

                while (queue.length) {{
                    const path = queue.shift();
                    const last = path[path.length - 1];
                    const neighbors = adjacency[last] || [];

                    for (const next of neighbors) {{
                        const nextId = String(next);
                        if (visited.has(nextId)) continue;

                        const newPath = [...path, nextId];
                        if (nextId === targetId) return newPath;

                        visited.add(nextId);
                        queue.push(newPath);
                    }}
                }}

                return null;
            }}

            function findBestPathToNode(targetId) {{
                let bestPath = null;

                for (const rootId of rootIds) {{
                    const path = bfsPathFromRoot(rootId, targetId);
                    if (!path) continue;

                    if (!bestPath || path.length < bestPath.length) {{
                        bestPath = path;
                    }}
                }}

                return bestPath;
            }}

            function ensureRootVisible(rootId) {{
                return treeRoot.querySelector(`.tree-node-item[data-instance-id="root-${{CSS.escape(String(rootId))}}"]`);
            }}

            function openPath(path) {{
                if (!path || !path.length) return null;

                const rootId = path[0];
                let currentInstance = ensureRootVisible(rootId);
                if (!currentInstance) return null;

                openNode(currentInstance);

                for (let i = 1; i < path.length; i++) {{
                    const targetNodeId = String(path[i]);

                    const children = Array.from(
                        currentInstance.querySelectorAll(':scope > .tree-node-body > .tree-children-list > .tree-node-item')
                    );

                    let nextInstance = children.find(child =>
                        String(child.dataset.graphNodeId) === targetNodeId
                    );

                    if (!nextInstance) return currentInstance;

                    openNode(nextInstance);
                    currentInstance = nextInstance;
                }}

                highlightInstance(currentInstance);
                return currentInstance;
            }}

            function focusNodeFromExternalSelection(nodeId) {{
                nodeId = String(nodeId);

                const bestPath = findBestPathToNode(nodeId);

                if (bestPath) {{
                    openPath(bestPath);
                    return;
                }}

                // fallback: if no root can reach the node, show/select first existing instance if any
                const existing = getAllInstancesForGraphNode(nodeId);
                if (existing.length) {{
                    highlightInstance(existing[0]);
                }}
            }}

            function escapeHtml(value) {{
                return value
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }}

            attachHandlersWithin(treeRoot);

            rootIds.forEach(rootId => {{
                const rootItem = ensureRootVisible(rootId);
                if (rootItem) {{
                    openNode(rootItem);
                }}
            }});

            const firstRoot = rootIds.length ? ensureRootVisible(rootIds[0]) : null;
            if (firstRoot) {{
                highlightInstance(firstRoot);
            }}

            window.addEventListener("graph-node-selected", function(event) {{
                const detail = event.detail || {{}};
                if (detail.workspaceId !== workspaceId) return;
                if (detail.nodeId == null) return;
                if (detail.source === "tree-view") return;

                focusNodeFromExternalSelection(detail.nodeId);
            }});
        }})();
        </script>
        """

    def _fallback_placeholder(self):
        return """
        <div class="tree-view-placeholder">
            <p>No graph data available.</p>
        </div>
        """