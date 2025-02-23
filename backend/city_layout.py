import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

class YieldCalculator:
    """
    Handles all yield-related calculations in one place.
    We keep it here so that CityLayout can call it without circular imports.
    """
    YIELD_TYPES = {"food", "production", "gold", "science", "culture", "happiness", "influence"}

    @staticmethod
    def create_empty_yields() -> Dict[str, float]:
        """Create a dict with all yields set to 0."""
        return {y: 0.0 for y in YieldCalculator.YIELD_TYPES}

    @staticmethod
    def combine_yields(base: Dict[str, float], modifier: Dict[str, float]) -> Dict[str, float]:
        """Combine two yield dictionaries, summing their values."""
        result = base.copy()
        for k, v in modifier.items():
            if k in result:
                result[k] += v
            else:
                result[k] = v
        return result

@dataclass
class Position:
    """Represents a position in the city grid."""
    ring: int
    index: int

@dataclass
class Tile:
    """Represents a single hex tile in the city."""
    position: Position
    terrain_type: str
    features: List[str]
    has_fresh_water: bool
    buildings: List[str] = None

    def __post_init__(self):
        self.buildings = self.buildings or []

class CityLayout:
    """
    Represents the entire city layout with all tiles, building data, etc.
    We define adjacency using a geometry-based approach:
      - ring=0..3
      - ring 1 => 6 tiles -> each tile angle = i*(360/6)
      - ring 2 => 12 tiles -> each tile angle = i*(360/12)
      - ring 3 => 18 tiles -> angle = i*(360/18)
    Then two tiles are adjacent if distance between centers < THRESHOLD.
    """

    N_TILES = {0: 1, 1: 6, 2: 12, 3: 18}
    RING_RADIUS = {0: 0.0, 1: 1.0, 2: 2.0, 3: 3.0}
    THRESHOLD = 1.2  # distance cutoff for adjacency

    def __init__(self):
        self.tiles: Dict[Tuple[int, int], Tile] = {}
        self._initialize_grid()
        self._load_game_data()

        # Precompute adjacency for all tiles
        self._adjacency_map: Dict[Tuple[int,int], List[Tuple[int,int]]] = {}
        self._build_adjacency_map()

    def _load_game_data(self):
        try:
            data_path = Path(__file__).parent / 'rules' / 'data'

            with open(data_path / 'buildings.json', 'r') as f:
                self.building_data = json.load(f)

            with open(data_path / 'terrain.json', 'r') as f:
                self.terrain_data = json.load(f)

            with open(data_path / 'wonders.json', 'r') as f:
                self.wonder_data = json.load(f)

        except Exception as e:
            print(f"Warning: Could not load game data: {e}")
            self.building_data = {}
            self.terrain_data = {}
            self.wonder_data = {}

    def _initialize_grid(self):
        """Create the 37 tiles (center + 3 rings)."""
        for r in range(4):
            for i in range(self.N_TILES[r]):
                self.tiles[(r, i)] = Tile(
                    position=Position(r, i),
                    terrain_type="",
                    features=[],
                    has_fresh_water=False
                )

    def _build_adjacency_map(self):
        """
        Compute adjacency for every tile by geometry:
          - Each tile center is ( ring_radius[r] * cos(angle), ring_radius[r] * sin(angle) )
          - angle = i * (360 / N_TILES[r])
          - Two tiles are neighbors if dist < THRESHOLD
        """
        # Gather centers
        centers: Dict[Tuple[int,int], Tuple[float,float]] = {}
        for r in range(4):
            n = self.N_TILES[r]
            for i in range(n):
                angle_deg = (360.0 / n) * i
                angle_rad = math.radians(angle_deg)
                radius = self.RING_RADIUS[r]
                x = radius * math.cos(angle_rad)
                y = radius * math.sin(angle_rad)
                centers[(r, i)] = (x, y)

        # Build adjacency by distance
        for r in range(4):
            for i in range(self.N_TILES[r]):
                pos1 = (r, i)
                c1 = centers[pos1]
                adj_list = []
                for rr in range(4):
                    for ii in range(self.N_TILES[rr]):
                        pos2 = (rr, ii)
                        if pos2 == pos1:
                            continue
                        c2 = centers[pos2]
                        dist = math.hypot(c2[0] - c1[0], c2[1] - c1[1])
                        if dist < self.THRESHOLD:
                            adj_list.append(pos2)
                self._adjacency_map[pos1] = adj_list

    def get_tile(self, ring: int, index: int) -> Optional[Tile]:
        return self.tiles.get((ring, index))

    def get_adjacent_positions(self, ring: int, index: int) -> List[Tuple[int,int]]:
        """Return the adjacency from our precomputed map."""
        return self._adjacency_map.get((ring, index), [])

    def get_adjacent_tiles(self, ring: int, index: int) -> List[Tile]:
        """Return the actual Tile objects for adjacent positions."""
        adj_pos = self.get_adjacent_positions(ring, index)
        return [self.tiles[p] for p in adj_pos if p in self.tiles]

    def set_tile_terrain(self, ring: int, index: int,
                         terrain_type: str, features: List[str],
                         has_fresh_water: bool):
        if (ring, index) in self.tiles:
            t = self.tiles[(ring, index)]
            t.terrain_type = terrain_type
            t.features = features
            t.has_fresh_water = has_fresh_water

    def is_valid_building_location(self, ring: int, index: int, building: str) -> bool:
        if building not in self.building_data:
            return False
        tile = self.get_tile(ring, index)
        if not tile:
            return False
        if not tile.terrain_type:
            return False
        if len(tile.buildings) >= 2:
            return False

        binfo = self.building_data[building]
        reqs = binfo.get('placement_requirements', {})

        # tile_type requirement
        if 'tile_type' in reqs:
            if tile.terrain_type not in reqs['tile_type']:
                return False

        # features requirement
        if 'features' in reqs:
            req_feats = set(reqs['features'])
            tile_feats = set(tile.features)
            if not req_feats.issubset(tile_feats):
                return False

        return True

    def add_building(self, ring: int, index: int, building: str) -> bool:
        if not self.is_valid_building_location(ring, index, building):
            return False
        self.tiles[(ring, index)].buildings.append(building)
        return True

    def _calculate_adjacency_yields(self, ring: int, index: int, building_info: Dict) -> Dict[str, float]:
        result = YieldCalculator.create_empty_yields()
        tile = self.get_tile(ring, index)
        if not tile:
            return result

        neighbors = self.get_adjacent_tiles(ring, index)
        for rule in building_info.get('adjacency_rules', []):
            sources = rule.get('sources', [])
            bonus_yields = rule.get('bonus_yields', {})
            match_count = 0

            # Check if current tile matches any source
            for src in sources:
                if src == "coastal_tile" and tile.terrain_type in ["coast","navigable_river","coastal_lake"]:
                    match_count += 1
                    break
                elif src == tile.terrain_type:
                    match_count += 1
                    break
                elif src in tile.features:
                    match_count += 1
                    break

            # Check neighbors
            for nbr in neighbors:
                for src in sources:
                    if src == "coastal_tile" and nbr.terrain_type in ["coast","navigable_river","coastal_lake"]:
                        match_count += 1
                        break
                    elif src == nbr.terrain_type:
                        match_count += 1
                        break
                    elif src in nbr.features:
                        match_count += 1
                        break

            # Apply bonus for each match
            for yld_type, val in bonus_yields.items():
                result[yld_type] += val * match_count

        return result

    def _calculate_quarter_yields(self, ring: int, index: int, building: str, building_info: Dict) -> Dict[str, float]:
        result = YieldCalculator.create_empty_yields()
        tile = self.get_tile(ring, index)
        if not tile:
            return result

        # If there's at least one building, add synergy
        for b in tile.buildings:
            if b == building:
                continue
            b_info = self.building_data.get(b, {})
            for yld, v in b_info.get('quarter_bonuses', {}).items():
                result[yld] += v

        for yld, v in building_info.get('quarter_bonuses', {}).items():
            result[yld] += v

        return result

    def calculate_building_yields(self, ring: int, index: int, building: str) -> Dict[str, Dict[str, float]]:
        if building not in self.building_data:
            return {
                "base_yields": {},
                "adjacency_yields": {},
                "quarter_yields": {},
                "total_yields": {}
            }

        tile = self.get_tile(ring, index)
        building_info = self.building_data[building]

        # 1) tile yields = 0 for an "urban" building
        tile_yields = YieldCalculator.create_empty_yields()

        # 2) base building yields
        base_yields = building_info.get("yields", {})

        # 3) adjacency yields
        adjacency = self._calculate_adjacency_yields(ring, index, building_info)

        # 4) quarter yields
        quarter = self._calculate_quarter_yields(ring, index, building, building_info)

        total = YieldCalculator.create_empty_yields()
        for k, v in tile_yields.items():
            total[k] += v
        for k, v in base_yields.items():
            total[k] += v
        for k, v in adjacency.items():
            total[k] += v
        for k, v in quarter.items():
            total[k] += v

        return {
            "base_yields": base_yields,
            "adjacency_yields": adjacency,
            "quarter_yields": quarter,
            "total_yields": total
        }
