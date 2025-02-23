from typing import Dict, Optional

# Maps UI colors to terrain types
COLOR_TO_TERRAIN: Dict[str, str] = {
    "#003366": "mountain",
    "#444444": "natural_wonder",
    "#5D4037": "resource",
    "#1E90FF": "open_ocean",
    "#66B3FF": "coast",
    "#00CED1": "coastal_lake",
    "#4682B4": "navigable_river",
    "#C5984C": "desert_flat",
    "#A67C39": "desert_rough",
    "#FFB347": "tropical_flat",
    "#FF8C69": "tropical_rough",
    "#566F18": "grassland_flat",
    "#4B5C16": "grassland_rough",
    "#9E9136": "plains_flat",
    "#8C7F30": "plains_rough",
    "#B8B8A4": "tundra_flat",
    "#A0A09A": "tundra_rough"
}

# Reverse mapping for converting terrain types back to colors
TERRAIN_TO_COLOR: Dict[str, str] = {v: k for k, v in COLOR_TO_TERRAIN.items()}

def get_terrain_from_color(color: str) -> Optional[str]:
    """Convert UI color to terrain type"""
    return COLOR_TO_TERRAIN.get(color)

def get_color_from_terrain(terrain: str) -> Optional[str]:
    """Convert terrain type to UI color"""
    return TERRAIN_TO_COLOR.get(terrain)

def get_terrain_category(terrain: str) -> Optional[str]:
    """Get the general category of a terrain type"""
    if not terrain:
        return None
    
    if '_' in terrain:
        base, variation = terrain.split('_')
    else:
        base = terrain
        
    # Map special types
    if base in ['coast', 'open_ocean', 'coastal_lake', 'navigable_river']:
        return 'water'
    if base == 'mountain':
        return 'mountain'
    if base == 'natural_wonder':
        return 'wonder'
    if base == 'resource':
        return 'resource'
        
    return base  # desert, tropical, grassland, plains, tundra