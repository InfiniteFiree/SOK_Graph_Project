class WorkspaceManager:
    def __init__(self):
        self._workspaces = {}
        self._active_workspace_id = None

    def add_workspace(self, workspace):
        self._workspaces[workspace.id] = workspace
        if self._active_workspace_id is None:
            self._active_workspace_id = workspace.id
        return workspace

    def get_workspace(self, workspace_id):
        return self._workspaces.get(workspace_id)

    def list_workspaces(self):
        return list(self._workspaces.values())

    def set_active(self, workspace_id):
        if workspace_id in self._workspaces:
            self._active_workspace_id = workspace_id

    def get_active(self):
        if self._active_workspace_id is None:
            return None
        return self._workspaces.get(self._active_workspace_id)

    def remove_workspace(self, workspace_id):
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            if self._active_workspace_id == workspace_id:
                self._active_workspace_id = next(iter(self._workspaces), None)