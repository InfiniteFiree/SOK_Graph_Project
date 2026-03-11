from abc import abstractmethod, ABC

from api.graph.api.model.graph import Graph


class Plugin(ABC):
    @abstractmethod
    def name(self) -> str:
        """
        Retrieves the name of the plugin.

        :return: The name of the plugin.
        :rtype: str
        """
        pass

    @abstractmethod
    def identifier(self) -> str:
        """
        Retrieves a unique identifier for the plugin.

        :return: The unique identifier of the plugin.
        :rtype: str
        """
        pass


class DataSourcePlugin(Plugin):
    """
    An abstraction representing a plugin for loading graph data from a specific data source.
    """

    @abstractmethod
    def load(self, **kwargs) -> Graph:
        """
        Loads data from the data source and returns it as a `Graph` object.

        :param kwargs: Arbitrary keyword arguments for customization or filtering of the data loading process.
        :type kwargs: dict
        :return: A `Graph` object loaded from the data source.
        :rtype: Graph
        """
        pass

class VisualizationPlugin(Plugin):
    """
    An abstraction representing a plugin for visualizing graph data in a specific way.
    """

    @abstractmethod
    def visualize(self, graph: Graph, **kwargs) -> str:
        """
        Visualizes the given `Graph` object and returns the visualization as a string (e.g., HTML).

        :param graph: The `Graph` object to be visualized.
        :type graph: Graph
        :param kwargs: Arbitrary keyword arguments for customization of the visualization process.
        :type kwargs: dict
        :return: A string representation of the visualization (e.g., HTML).
        :rtype: str
        """
        pass
