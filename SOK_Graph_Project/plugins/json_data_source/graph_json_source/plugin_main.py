from api.build.lib.graph.api.services.plugin import DataSourcePlugin
from core.build.lib.service.use_cases.data_source_service import DataSourceService


class JsonDataSourcePlugin(DataSourcePlugin):

    def name(self) -> str:
        return "JSON Data Source"

    def identifier(self) -> str:
        return "json"

    def load(self, **kwargs):

        source_path = kwargs.get("source_path")

        source_path = DataSourceService.require_existing_file(
            source_path,
            ".json"
        )

        data = DataSourceService.read_json(source_path)

        return DataSourceService.dict_to_graph(data)

    def save(self, graph, **kwargs):

        source_path = kwargs.get("source_path")

        payload = DataSourceService.graph_to_dict(graph)

        DataSourceService.write_json(source_path, payload)