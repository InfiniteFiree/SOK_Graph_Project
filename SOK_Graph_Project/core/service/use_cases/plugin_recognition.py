from api.graph.api.services.plugin import get_visualizer

def recognize_plugin(user_preference: str = None):
    """
    Prepoznaje koji vizualizer treba koristiti.
    Ako nije prosleđen preference, vraća default (block).
    """
    plugin_type = user_preference or "block"
    return get_visualizer(plugin_type)