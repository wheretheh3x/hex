from typing import Dict, List, Optional, Union, TypedDict, Literal

class Yields(TypedDict, total=False):
    food: float
    production: float
    gold: float
    science: float
    culture: float
    faith: float
    happiness: float

# Biome types
BiomeType = Literal["Plains", "Grassland", "Tropical", "Desert", "Tundra", "Marine"]

# Terrain variations
TerrainVariation = Literal["Flat", "Rough", "Mountainous"]

# Features that can appear on terrain
class TerrainFeature(TypedDict):
    name: str  # e.g., "Forest", "Marsh", "Oasis"
    category: Literal["Minor River", "Wet", "Vegetated", "Floodplain", "Reef"]
    movement_difficulty: bool
    provides_fresh_water: bool
    biome_specific: bool  # If True, this feature only appears in specific biomes
    valid_biomes: List[BiomeType]  # Which biomes this feature can appear in
    base_yields: Yields
    additional_attributes: Dict[str, Union[str, bool, float]]

class TerrainType(TypedDict):
    biome: BiomeType
    variation: TerrainVariation
    is_water: bool  # True for Marine biome
    base_yields: Yields
    is_buildable: bool
    valid_features: List[str]  # Which features can appear on this terrain
    movement_cost: float
    elevation_level: int  # For river flow and cliff generation
    additional_attributes: Dict[str, Union[str, bool, float]]

# Special case for Marine biome variations
class MarineType(TerrainType):
    marine_category: Literal["Coastal", "Open Ocean", "Coastal Lake", "Navigable River"]
    connects_to_ocean: bool

# Actual tile instance in a city
class Tile(TypedDict):
    terrain_type: str  # references TerrainType
    features: List[str]  # List of TerrainFeature names present on this tile
    has_fresh_water: bool  # Combined result of features and adjacent tiles
    position: Dict[str, int]  # ring and index in the ring
    elevation: int  # For determining river flow
    resources: List[str]  # Resources present on the tile
