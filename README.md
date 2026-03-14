# SOK_Graph_Project
### Project for the visualization of graphs in space, utilizing plug-ins for the main functions of the app.

## Team 8 - members
- SV 28/2023	Marko	Đorđević
- SV 79/2023	Aleksa	Nenadović
- SV 85/2024	Lana	Vuković
- SV 82/2024	Luka	Berić

## How to run flask app:
### - First, run: 

```shell
python -m venv venv
```

### then:

```shell
.\venv\Scripts\activate
```

### both while inside the flask folder.

### - Then, to install the libraries and plugins required, use:

```shell
pip install -r requirements.txt
```

### and then:

```shell
pip install ./api ./core ./plugins/simple_visualizer ./plugins/block_visualizer ./plugins/csv_data_source ./plugins/json_data_source
```

### - In case that this is the first time running the app, use:

```shell
cd flask
set FLASK_APP=app.py
```

### - Finally, whenever you want the app to run, use 

```shell
flask run
``` 

### while inside the flask folder.

## Plugin Development Guide

The application supports external plugins for extending functionality without modifying the core system.

Currently two plugin types exist:

- Visualization plugins – render graphs in different visual formats

- Data source plugins – load graphs from different file formats or sources

Plugins are installed using pip and are automatically discovered by the application.

### Creating a Visualization Plugin

Visualization plugins control how the graph is displayed.

They must inherit from:

```txt
VisualizationPlugin
```

Example:

```py
from api.build.lib.graph.api.services.plugin import VisualizationPlugin
from api.build.lib.graph.api.model.graph import Graph


class MyVisualizer(VisualizationPlugin):

    def name(self) -> str:
        return "My Custom Visualizer"

    def identifier(self) -> str:
        return "my_visualizer"

    def visualize(self, graph: Graph, **kwargs) -> dict:
        return {
            "plugin_id": self.identifier(),
            "graph": {
                "nodes": [],
                "edges": []
            },
            "options": {}
        }
```

The visualize() method must return a dictionary that the frontend renderer can interpret.

### Creating a Data Source Plugin

Data source plugins define how graphs are loaded.

They must inherit from:

```txt
DataSourcePlugin
```

Example:

```py
from sok_graph_api.graph.api.services.plugin import DataSourcePlugin


class MyDataSourcePlugin(DataSourcePlugin):

    def name(self) -> str:
        return "My Data Source"

    def identifier(self) -> str:
        return "my_data_source"

    def load(self, **kwargs):
        source_path = kwargs.get("source_path")

        if not source_path:
            raise ValueError("source_path is required")

        # Load your graph here

        return graph
```

The load() function must return a Graph object.

### Plugin Project Structure

Each plugin should be its own installable Python package.

Example structure:

```txt
my_visualizer_plugin/
│
├── pyproject.toml
└── my_visualizer_plugin
    ├── __init__.py
    └── my_visualizer.py
```

Example for a data source plugin:

```txt
my_json_plugin/
│
├── pyproject.toml
└── my_json_plugin
    ├── __init__.py
    └── json_plugin.py
```

Example pyproject.toml

Example for a visualization plugin:

```txt
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-graph-visualizer"
version = "1.0.0"
description = "Custom graph visualizer plugin"
requires-python = ">=3.10"

dependencies = [
    "sok-graph-api"
]

[tool.setuptools.packages.find]
where = ["."]
include = ["my_visualizer_plugin*"]
```