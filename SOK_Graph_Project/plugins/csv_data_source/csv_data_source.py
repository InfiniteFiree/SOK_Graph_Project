import json
import os
from api.graph.api.services.plugin import DataSourcePlugin
from plugins.csv_data_source.csv_db.csv_db import CsvDb


class CsvDataSourcePlugin(DataSourcePlugin):
    def name(self) -> str:
        return "CSV Data Source"

    def identifier(self) -> str:
        return "csv"

    def load(self, **kwargs):
        source_path = kwargs.get("source_path")
        if not source_path:
            raise ValueError("source_path is required for CSV data source")

        source_path = os.path.abspath(source_path)

        # Case 1: single CSV file
        if os.path.isfile(source_path):
            csv_db = CsvDb(
                mode="single_file",
                csv_path=source_path
            )
            return csv_db.load()

        # Case 2: folder containing nodes.csv and edges.csv
        if os.path.isdir(source_path):
            nodes_path = os.path.join(source_path, "nodes.csv")
            edges_path = os.path.join(source_path, "edges.csv")

            if not os.path.isfile(nodes_path) or not os.path.isfile(edges_path):
                raise ValueError(
                    f"CSV folder '{source_path}' must contain both nodes.csv and edges.csv"
                )

            # Optional metadata support
            # If graph.json exists, use it to determine directed flag.
            directed = True
            metadata_path = os.path.join(source_path, "graph.json")

            if os.path.isfile(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                directed = bool(metadata.get("directed", True))

            csv_db = CsvDb(
                mode="separate_files",
                nodes_path=nodes_path,
                edges_path=edges_path,
                directed=directed
            )
            return csv_db.load()

        raise ValueError(f"Invalid CSV source_path: {source_path}")