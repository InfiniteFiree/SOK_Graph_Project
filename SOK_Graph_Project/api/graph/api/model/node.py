
from dataclasses import dataclass

@dataclass
class Node:

    def __init__(self, data=None, index=None):
        self.data = data
        self.index = index
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = self._normalizeData(value)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    def addData(self, key, value):
        self.data[key] = value

    def removeData(self, key):
        if key not in self.data:
            raise KeyError(f"Key '{key}' does not exist in node data")
        del self.data[key]

    def toString(self):
        return f"Node(data={self.data}, index={self.index})"

    def __str__(self):
        return self.toString()

    def _normalizeData(self, data):
        if data is None:
            return {}
        try:
            return dict(data)
        except Exception as exc:
            raise ValueError("Node data must be a dictionary or dictionary-compatible value") from exc