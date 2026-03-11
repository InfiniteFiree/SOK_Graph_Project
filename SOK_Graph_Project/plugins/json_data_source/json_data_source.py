from api.graph.api.services.plugin import DataSourcePlugin
from plugins.json_data_source.json_db.json_db import JSONRepository  # prilagodi putanju

class JsonDataSource(DataSourcePlugin):
    def __init__(self):
        self.repo = JSONRepository("test_graph.json")  # ili konfigurabilno

    def identifier(self):
        return "json"  # ovo se koristi u query parametru

    def name(self):
        return "JSON Data Source"

    def load(self):
        graph = self.repo.read_from_file()
        return graph