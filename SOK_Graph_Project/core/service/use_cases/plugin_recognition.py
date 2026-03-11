from typing import List
import os
import sys
import importlib

from api.graph.api.services.plugin import Plugin, DataSourcePlugin, VisualizationPlugin

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

PLUGIN_FOLDER = os.path.join(PROJECT_ROOT, "plugins")
PARENT_FOLDER = PROJECT_ROOT

# Dodaj root u sys.path ako već nije
if PARENT_FOLDER not in sys.path:
    sys.path.insert(0, PARENT_FOLDER)


class PluginService(object):

    def __init__(self):
        self.plugins = {
            "visualization": {},
            "data_source": {}
        }

    def load_plugins(self):

        # očisti prethodne plugine (korisno kod Flask debug reload)
        self.plugins["visualization"].clear()
        self.plugins["data_source"].clear()

        # Prođi kroz sve .py fajlove u PLUGIN_FOLDER i podfolderima
        for root, _, files in os.walk(PLUGIN_FOLDER):
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py"]:
                    rel_path = os.path.relpath(os.path.join(root, file), PARENT_FOLDER)
                    module_name = rel_path[:-3].replace(os.sep, ".")

                    try:
                        if module_name in sys.modules:
                            module = importlib.reload(sys.modules[module_name])
                        else:
                            module = importlib.import_module(module_name)
                    except Exception as e:
                        print(f"[plugin_recognition] Warning: Failed to import {module_name}: {e}")
                        continue

                    # traži sve klase koje nasledjuju Plugin
                    for attr in dir(module):
                        obj = getattr(module, attr)

                        if isinstance(obj, type) and issubclass(obj, Plugin) and obj != Plugin:
                            try:
                                instance = obj()
                            except TypeError:
                                continue

                            if isinstance(instance, VisualizationPlugin):
                                self.plugins["visualization"][instance.identifier()] = instance

                            elif isinstance(instance, DataSourcePlugin):
                                self.plugins["data_source"][instance.identifier()] = instance

        return self.plugins