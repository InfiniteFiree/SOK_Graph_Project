import html
import json


class TreeView:
    """
    Lazy tree view:
    - renders only one root initially
    - children are loaded into the DOM only when a node is opened
    - children are derived only from outgoing edges (node1 -> node2)
    - reacts to graph-node-selected from the main view
    """

    def __init__(self, graph=None):
        self.graph = graph

    def render(self):
        if self.graph is None or not getattr(self.graph, "nodes", None):
            return self._fallback_placeholder()

        node_map = self._build_node_map()
        adjacency = self._build_outgoing_adjacency()
        root_id = self._choose_root_id()

        if root_id is None:
            return self._fallback_placeholder()

        return self._render_lazy_tree(node_map, adjacency, root_id)

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

        for node_id in adjacency:
            adjacency[node_id] = sorted(adjacency[node_id], key=self._sort_key)

        return adjacency

    def _choose_root_id(self):
        nodes = self.graph.nodes or []
        if not nodes:
            return None

        indegree = {str(node.index): 0 for node in nodes}

        for edge in getattr(self.graph, "edges", []) or []:
            if edge.node1 is None or edge.node2 is None:
                continue
            target_id = str(edge.node2.index)
            if target_id in indegree:
                indegree[target_id] += 1

        zero_indegree = [
            str(node.index)
            for node in nodes
            if indegree[str(node.index)] == 0
        ]

        if zero_indegree:
            return sorted(zero_indegree, key=self._sort_key)[0]

        return sorted((str(node.index) for node in nodes), key=self._sort_key)[0]

    def _sort_key(self, value):
        try:
            return (0, int(value))
        except Exception:
            return (1, str(value))

    def _render_lazy_tree(self, node_map, adjacency, root_id):
        node_map_json = json.dumps(node_map)
        adjacency_json = json.dumps(adjacency)
        root_id_escaped = html.escape(str(root_id))

        return f"""
        <div id="tree-view-root" class="tree-view-root" data-root-id="{root_id_escaped}">
            <ul class="tree-root-list">
                <li class="tree-node-item open selected"
                    data-node-id="{root_id_escaped}"
                    data-parent-id="">
                    <div class="tree-node-header">
                        <button type="button" class="tree-toggle" data-role="toggle">-</button>
                        <span class="tree-node-title">id: {root_id_escaped}</span>
                    </div>
                    <div class="tree-node-body"></div>
                </li>
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
            const nodeMap = {node_map_json};
            const adjacency = {adjacency_json};

            const treeRoot = document.getElementById("tree-view-root");
            if (!treeRoot) return;

            let currentRootId = String(treeRoot.dataset.rootId);

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

            function findItem(nodeId) {{
                return treeRoot.querySelector(`.tree-node-item[data-node-id="${{CSS.escape(String(nodeId))}}"]`);
            }}

            function clearSelection() {{
                treeRoot.querySelectorAll(".tree-node-item.selected").forEach(el => {{
                    el.classList.remove("selected");
                }});
            }}

            function highlightNode(nodeId) {{
                clearSelection();
                const item = findItem(nodeId);
                if (!item) return;
                item.classList.add("selected");
                item.scrollIntoView({{
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

            function buildDataHtml(nodeId) {{
                const node = nodeMap[nodeId];
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

            function buildChildrenShellHtml(nodeId) {{
                const children = sortIds(adjacency[nodeId] || []);
                if (!children.length) return "";

                const items = children.map(childId => `
                    <li class="tree-node-item"
                        data-node-id="${{escapeHtml(String(childId))}}"
                        data-parent-id="${{escapeHtml(String(nodeId))}}">
                        <div class="tree-node-header">
                            <button type="button" class="tree-toggle" data-role="toggle">+</button>
                            <span class="tree-node-title">id: ${{escapeHtml(String(childId))}}</span>
                        </div>
                        <div class="tree-node-body"></div>
                    </li>
                `).join("");

                return `
                    <div class="tree-section-label">children:</div>
                    <ul class="tree-children-list">${{items}}</ul>
                `;
            }}

            function ensureNodeContentBuilt(item) {{
                if (!item) return;
                if (item.dataset.built === "true") return;

                const nodeId = item.dataset.nodeId;
                const body = item.querySelector(':scope > .tree-node-body');
                if (!body) return;

                body.innerHTML = buildDataHtml(nodeId) + buildChildrenShellHtml(nodeId);
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

                            const nodeId = item.dataset.nodeId;
                            const isOpen = item.classList.contains("open");

                            if (isOpen) {{
                                closeNode(item);
                            }} else {{
                                openNode(item);
                                selectAndBroadcast(nodeId);
                            }}
                        }});
                    }}

                    if (header) {{
                        header.addEventListener("click", function() {{
                            const nodeId = item.dataset.nodeId;
                            openNode(item);
                            selectAndBroadcast(nodeId);
                        }});
                    }}
                }});
            }}

            function selectAndBroadcast(nodeId) {{
                highlightNode(nodeId);

                window.dispatchEvent(new CustomEvent("graph-node-selected", {{
                    detail: {{
                        nodeId: String(nodeId),
                        source: "tree-view",
                        panTo: true
                    }}
                }}));
            }}

            function bfsPath(startId, targetId) {{
                startId = String(startId);
                targetId = String(targetId);

                if (startId === targetId) return [startId];

                const queue = [[startId]];
                const visited = new Set([startId]);

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

            function renderFreshRoot(newRootId) {{
                currentRootId = String(newRootId);
                treeRoot.dataset.rootId = currentRootId;

                const rootList = treeRoot.querySelector(".tree-root-list");
                rootList.innerHTML = `
                    <li class="tree-node-item open selected"
                        data-node-id="${{escapeHtml(currentRootId)}}"
                        data-parent-id="">
                        <div class="tree-node-header">
                            <button type="button" class="tree-toggle" data-role="toggle">-</button>
                            <span class="tree-node-title">id: ${{escapeHtml(currentRootId)}}</span>
                        </div>
                        <div class="tree-node-body"></div>
                    </li>
                `;

                const rootItem = findItem(currentRootId);
                openNode(rootItem);
                highlightNode(currentRootId);
            }}

            function openPath(path) {{
                if (!path || !path.length) return;

                for (const nodeId of path) {{
                    const item = findItem(nodeId);
                    if (item) {{
                        openNode(item);
                    }}
                }}

                highlightNode(path[path.length - 1]);
            }}

            function focusNodeFromExternalSelection(nodeId) {{
                nodeId = String(nodeId);

                let path = bfsPath(currentRootId, nodeId);

                if (path) {{
                    openPath(path);
                    return;
                }}

                // fallback for cyclic/disconnected situations:
                // selected node becomes the new root
                renderFreshRoot(nodeId);
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

            const initialRootItem = findItem(currentRootId);
            if (initialRootItem) {{
                openNode(initialRootItem);
                highlightNode(currentRootId);
            }}

            window.addEventListener("graph-node-selected", function(event) {{
                const detail = event.detail || {{}};
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