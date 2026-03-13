import os

from api.graph.api.services.plugin import DataSourcePlugin
from plugins.json_data_source.json_db.json_db import JSONRepository


class JsonDataSourcePlugin(DataSourcePlugin):
    def name(self) -> str:
        return "JSON Data Source"

    def identifier(self) -> str:
        return "json"

    def load(self, **kwargs):
        source_path = kwargs.get("source_path")
        if not source_path:
            raise ValueError("source_path is required for JSON data source")

        source_path = os.path.abspath(source_path)

        if not os.path.isfile(source_path):
            raise ValueError(f"JSON file does not exist: {source_path}")

        repo = JSONRepository(source_path)
        graph = repo.read_from_file()

        if graph is None:
            raise ValueError(f"Failed to load JSON graph from: {source_path}")

        return graph