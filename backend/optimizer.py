# optimizer.py

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from backend.city_layout import CityLayout, YieldCalculator

@dataclass
class OptimizationResult:
    position: Tuple[int, int]  # ring, index
    building: str
    yields: Dict[str, Dict[str, float]]
    score: float

class CityOptimizer:
    """Handles optimization of building placement using a backtracking approach."""

    def __init__(self, city_layout: CityLayout):
        self.city = city_layout

        # We'll keep track of best arrangement across the recursion
        self.best_score: float = float("-inf")
        # A list of tuples: (building_name, (ring, index)) for each placed building
        self.best_arrangement: List[Tuple[str, Tuple[int, int]]] = []

    def optimize_multiple_buildings(
        self,
        buildings: List[str],
        yield_priorities: Dict[str, float] = None
    ) -> List[OptimizationResult]:
        """
        Main entry point for global optimization of multiple buildings
        using backtracking. Returns a list of OptimizationResult describing
        each building's final chosen position and yields.

        If skipping a building is allowed, we handle that in the recursion.
        """

        if yield_priorities is None:
            # If user didn't specify, give each yield type a priority of 1.0
            yield_priorities = {y: 1.0 for y in YieldCalculator.YIELD_TYPES}

        # Clear out old best arrangement
        self.best_score = float("-inf")
        self.best_arrangement = []

        # Start recursion from the first building
        # We'll pass along a "current arrangement" that we build up
        self._backtrack_place_building(
            buildings=buildings,
            current_idx=0,
            yield_priorities=yield_priorities,
            current_arrangement=[]
        )

        # Build final results
        final_results: List[OptimizationResult] = []
        for (bldg, (ring, idx)) in self.best_arrangement:
            # We can recalc yields for display
            yds = self.city.calculate_building_yields(ring, idx, bldg)
            score_val = self._calculate_position_score(yds['total_yields'], yield_priorities)
            result = OptimizationResult(
                position=(ring, idx),
                building=bldg,
                yields=yds,
                score=score_val
            )
            final_results.append(result)

        return final_results

    def _backtrack_place_building(
        self,
        buildings: List[str],
        current_idx: int,
        yield_priorities: Dict[str, float],
        current_arrangement: List[Tuple[str, Tuple[int, int]]]
    ):
        """
        Recursive function to try all ways of placing building `buildings[current_idx]`.
        We can also skip placing it entirely, if that's allowed by game rules.

        Once we've assigned all buildings, we compute the total yield-based score
        and update `self.best_arrangement` if we found a better solution.
        """

        # If we've processed all buildings, evaluate the arrangement's total score
        if current_idx >= len(buildings):
            total_score = self._score_entire_arrangement(current_arrangement, yield_priorities)
            if total_score > self.best_score:
                self.best_score = total_score
                self.best_arrangement = current_arrangement.copy()
            return

        building = buildings[current_idx]

        # 1) Option to skip placing this building
        #    If the game always allows skipping, do so:
        self._backtrack_place_building(
            buildings,
            current_idx + 1,
            yield_priorities,
            current_arrangement
        )

        # 2) Try placing the building on each valid tile
        for ring in range(4):  # ring = 0..3
            max_idx = 1 if ring == 0 else 6 * ring
            for idx in range(max_idx):
                if self.city.is_valid_building_location(ring, idx, building):
                    # Temporarily place building
                    self.city.add_building(ring, idx, building)
                    current_arrangement.append((building, (ring, idx)))

                    # Recurse for next building
                    self._backtrack_place_building(
                        buildings,
                        current_idx + 1,
                        yield_priorities,
                        current_arrangement
                    )

                    # BACKTRACK: remove building
                    current_arrangement.pop()
                    tile = self.city.get_tile(ring, idx)
                    if tile and building in tile.buildings:
                        tile.buildings.remove(building)

    def _score_entire_arrangement(
        self,
        arrangement: List[Tuple[str, Tuple[int, int]]],
        yield_priorities: Dict[str, float]
    ) -> float:
        """
        Compute the total score for a given arrangement. Because adjacency
        depends on the presence of other buildings, we rely on the fact that
        we've physically placed them in self.city's tiles as well.
        """
        total_score = 0.0
        for (bldg, (r, i)) in arrangement:
            all_yields = self.city.calculate_building_yields(r, i, bldg)
            total_score += self._calculate_position_score(all_yields['total_yields'], yield_priorities)
        return total_score

    def _calculate_position_score(
        self,
        yields: Dict[str, float],
        priorities: Dict[str, float]
    ) -> float:
        """
        Weighted sum of yields. Example: total_score += yields["culture"] * priorities["culture"] ...
        """
        score = 0.0
        for yld_type, amount in yields.items():
            prio = priorities.get(yld_type, 0.0)
            score += amount * prio
        return score
