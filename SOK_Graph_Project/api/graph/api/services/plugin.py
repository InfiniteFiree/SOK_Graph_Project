from block_visualizer.block_visualizer import BlockVisualizer
from simple_visualizer.simple_visualizer import SimpleVisualizer

def get_visualizer(plugin_type: str):
    """Vrati instancu vizualizera na osnovu tipa plugin-a."""
    if plugin_type == "block":
        return BlockVisualizer()
    elif plugin_type == "simple":
        return SimpleVisualizer()
    else:
        return BlockVisualizer()