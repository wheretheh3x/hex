import pytest
from backend.city_layout import CityLayout
from backend.optimizer import CityOptimizer

def print_grid(city):
    """Print a simple ASCII representation of the city grid"""
    print("\nCity Layout:")
    print("   Ring 0 (Center):")
    tile = city.get_tile(0, 0)
    print(f"      Terrain: {tile.terrain_type}")
    print(f"      Buildings: {tile.buildings}")
    
    print("\n   Ring 1:")
    for i in range(6):
        tile = city.get_tile(1, i)
        print(f"      Position {i}: Terrain: {tile.terrain_type}, Buildings: {tile.buildings}")
    
    print("\n   Ring 2:")
    for i in range(12):
        tile = city.get_tile(2, i)
        print(f"      Position {i}: Terrain: {tile.terrain_type}, Buildings: {tile.buildings}")

def test_visual_monument():
    """
    Visual test of placing a single building with minimal constraints.
    Using 'monument' as an example, but feel free to pick any building 
    with simple or no placement requirements.
    """
    print("\n=== Testing Monument Placement ===")
    
    city = CityLayout()
    optimizer = CityOptimizer(city)
    
    print("\nSetting up terrain...")
    # Give the center tile a simple terrain
    city.set_tile_terrain(0, 0, "plains_flat", [], False)
    # A few ring-1 tiles with different terrain
    city.set_tile_terrain(1, 0, "plains_flat", [], False)
    city.set_tile_terrain(1, 1, "mountain", [], False)
    city.set_tile_terrain(1, 2, "plains_flat", [], False)
    
    print_grid(city)
    
    print("\nTrying to place monument...")
    # If using your new global solver for a single building:
    #   result = optimizer.optimize_building_placement("monument", yield_priorities={"culture": 1.0})
    #   # ...the old single-building approach
    # 
    # Or if you want to use the backtracking approach (which can place or skip),
    # just do:
    results = optimizer.optimize_multiple_buildings(
        ["monument"],
        yield_priorities={"culture": 1.0}
    )
    
    if results:
        # Since there's only one building in the list, results[0] is it
        result = results[0]
        print("\nOptimization Result:")
        print(f"Selected Position: Ring {result.position[0]}, Index {result.position[1]}")
        print("\nYields:")
        print("  Base yields:", result.yields['base_yields'])
        print("  Adjacency yields:", result.yields['adjacency_yields'])
        print("  Quarter yields:", result.yields['quarter_yields'])
        print("  Total yields:", result.yields['total_yields'])
    else:
        print("\nNo placement found (the solver might have skipped it or no valid tile).")

def test_visual_two_buildings():
    """
    Visual test of placing two buildings globally.
    We'll pick 'monument' and 'arena' as an example, 
    ignoring adjacency if they have no synergy.
    """
    print("\n=== Testing Two-Building Placement (Monument + Arena) ===")
    
    city = CityLayout()
    optimizer = CityOptimizer(city)
    
    print("\nSetting up terrain...")
    # Give the center tile some terrain
    city.set_tile_terrain(0, 0, "plains_flat", [], False)
    # A few ring-1 tiles with different terrain
    city.set_tile_terrain(1, 0, "plains_flat", [], False)
    city.set_tile_terrain(1, 1, "mountain", [], False)
    city.set_tile_terrain(1, 2, "plains_flat", [], False)
    
    print_grid(city)
    
    print("\nTrying to place monument and arena...")
    results = optimizer.optimize_multiple_buildings(
        ["monument", "arena"],
        yield_priorities={"culture": 1.0, "happiness": 0.8}
    )
    
    if not results:
        print("\nNo buildings placed — solver found no valid spots or skipping was best.")
        return
    
    for i, result in enumerate(results):
        print(f"\nBuilding {i+1} ({result.building}):")
        print(f"Selected Position: Ring {result.position[0]}, Index {result.position[1]}")
        print("\nYields:")
        print("  Base yields:", result.yields['base_yields'])
        print("  Adjacency yields:", result.yields['adjacency_yields'])
        print("  Quarter yields:", result.yields['quarter_yields'])
        print("  Total yields:", result.yields['total_yields'])
