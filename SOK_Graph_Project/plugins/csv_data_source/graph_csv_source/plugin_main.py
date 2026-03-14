import csv
import os

from graph.api.services.plugin import DataSourcePlugin
from service.use_cases.data_source_service import DataSourceService


class CsvDataSourcePlugin(DataSourcePlugin):

    def name(self):
        return "CSV Data Source"

    def identifier(self):
        return "csv"

    def load(self, **kwargs):

        source_path = kwargs.get("source_path")

        source_path = DataSourceService.require_source_path(source_path)

        if os.path.isfile(source_path):
            return self._load_single_csv(source_path)

        if os.path.isdir(source_path):
            return self._load_csv_folder(source_path)

        raise ValueError(f"Invalid CSV source_path: {source_path}")

    # --------------------------------------------------
    # SINGLE CSV
    # --------------------------------------------------

    def _load_single_csv(self, path):

        nodes = []
        edges = []

        with open(path, newline="", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            for row in reader:

                node_id = row.get("id")

                if not node_id:
                    continue

                nodes.append({
                    "index": node_id,
                    "data": {
                        k: v for k, v in row.items()
                        if k not in ["id", "connected_to"]
                    }
                })

                refs = row.get("connected_to", "")

                if refs:

                    for target in refs.split(","):
                        edges.append((node_id, target.strip()))

        return DataSourceService.build_graph(nodes, edges)

    # --------------------------------------------------
    # NODES + EDGES CSV
    # --------------------------------------------------

    def _load_csv_folder(self, directory):

        files = DataSourceService.require_files(
            directory,
            ["nodes.csv", "edges.csv"]
        )

        nodes = []
        edges = []

        with open(files["nodes.csv"], newline="", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            for row in reader:

                node_id = row.get("id")

                if not node_id:
                    continue

                nodes.append({
                    "index": node_id,
                    "data": {
                        k: v for k, v in row.items()
                        if k != "id"
                    }
                })

        with open(files["edges.csv"], newline="", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            for row in reader:

                source = row.get("source")
                target = row.get("target")

                if source and target:
                    edges.append((source, target))

        directed = True

        metadata_path = os.path.join(directory, "graph.json")

        if os.path.isfile(metadata_path):

            metadata = DataSourceService.read_json(metadata_path)

            directed = bool(metadata.get("directed", True))

        return DataSourceService.build_graph(
            nodes,
            edges,
            directed
        )