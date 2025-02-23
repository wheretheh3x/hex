from typing import Dict, List, Optional, Union

class TerrainType:
    """Represents different types of terrain in the game."""
    PLAINS = "plains"
    GRASSLAND = "grassland"
    MOUNTAIN = "mountain"
    OCEAN = "ocean"
    RIVER = "river"
    # Add more as needed

class Building:
    """
    Represents a building in the game with its properties and requirements.
    """
    def __init__(
        self,
        name: str,
        base_yields: Dict[str, float],
        placement_requirements: List[str],
        era: str = "ancient",
        can_form_quarter: bool = True
    ):
        self.name = name
        self.base_yields = base_yields  # e.g., {"culture": 4, "food": 1}
        self.placement_requirements = placement_requirements  # e.g., ["grassland", "plains"]
        self.era = era
        self.can_form_quarter = can_form_quarter

class AdjacencyRule:
    """
    Represents an adjacency bonus rule.
    """
    def __init__(
        self,
        source: str,  # Building or terrain providing the bonus
        target: str,  # Building receiving the bonus
        yields: Dict[str, float],  # e.g., {"culture": 1, "happiness": 1}
        conditions: Optional[Dict[str, str]] = None  # Additional conditions
    ):
        self.source = source
        self.target = target
        self.yields = yields
        self.conditions = conditions or {}