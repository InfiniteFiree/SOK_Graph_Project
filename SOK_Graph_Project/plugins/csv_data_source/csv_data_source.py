from api.graph.api.services.plugin import DataSourcePlugin
from plugins.csv_data_source.csv_db.csv_db import CsvDb

class CsvDataSource(DataSourcePlugin):
    def __init__(self):
        self.db = CsvDb(mode="separate_files")  # default ili konfiguracija po potrebi

    def identifier(self):
        return "csv"

    def name(self):
        return "CSV Data Source"

    def load(self):
        return self.db.load()