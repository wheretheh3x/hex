import pytest
from backend.city_layout import CityLayout
from backend.optimizer import CityOptimizer

def verify_yields(description: str, expected: dict, actual: dict):
    """Helper to verify and print yield comparisons"""
    print(f"\n{description}:")
    print(f"  Expected: {expected}")
    print(f"  Actual  : {actual}")
    for key in expected:
        assert key in actual, f"Missing yield type: {key}"
        assert expected[key] == actual[key], f"Wrong {key} yield. Expected {expected[key]}, got {actual[key]}"

def test_arena_yields():
    """
    Verify exact yield calculations for 'arena' placement.
    'arena' has a base yield of {"happiness": 4}, plus
    adjacency to mountain => +1 happiness
    """
    print("\n=== Verifying Arena Yields ===")

    city = CityLayout()

    # Setup test scenario
    # We'll place a mountain in (1,0) and check adjacency from (1,1).
    city.set_tile_terrain(1, 0, "mountain", [], False)       # Mountain
    city.set_tile_terrain(1, 1, "plains_flat", [], False)    # Plains next to mountain
    city.set_tile_terrain(1, 2, "plains_flat", [], False)    # Plains not next to mountain

    # Calculate yields for position adjacent to mountain
    print("\nTesting position adjacent to mountain (1,1):")
    yields_adj = city.calculate_building_yields(1, 1, "arena")

    # Verify base yields (arena base = {"happiness": 4})
    verify_yields("Base yields",
                  {"happiness": 4},
                  yields_adj["base_yields"])

    # Verify adjacency yields from mountain => +1 happiness
    verify_yields("Adjacency yields",
                  {"happiness": 1},
                  yields_adj["adjacency_yields"])

    # Now test position NOT next to mountain (1,2)
    print("\nTesting position NOT adjacent to mountain (1,2):")
    yields_no_adj = city.calculate_building_yields(1, 2, "arena")

    # No adjacency bonus
    verify_yields("Adjacency yields (should be none)",
                  {"happiness": 0},
                  yields_no_adj["adjacency_yields"])

def test_garden_and_bath_yields():
    """
    Verify exact yield calculations for 'garden' and 'bath' placement.
    Each has base yields of food, plus adjacency bonus from 'coastal_tile' => +1 food.
    'garden': base_yields {"food": 3}, adjacency {"food": 1}
    'bath':   base_yields {"food": 4}, adjacency {"food": 1}
    They also get quarter synergy if they share a tile, which we can check.
    """
    print("\n=== Verifying Garden and Bath Yields ===")

    city = CityLayout()

    # Setup test scenario
    # Let's designate (1,0) as coast for adjacency
    city.set_tile_terrain(1, 0, "coast", [], True)

    # Test garden yields
    print("\nTesting garden on coastal tile (1,0):")
    yields_garden = city.calculate_building_yields(1, 0, "garden")

    # 'garden' base yields => {"food": 3}
    verify_yields("Garden base yields",
                  {"food": 3},
                  yields_garden["base_yields"])

    # adjacency => +1 food from coastal_tile
    verify_yields("Garden adjacency yields",
                  {"food": 1},
                  yields_garden["adjacency_yields"])

    # Place garden, then test bath yields
    city.add_building(1, 0, "garden")
    print("\nTesting bath placement with garden on tile (1,0):")
    yields_bath = city.calculate_building_yields(1, 0, "bath")

    # 'bath' base yields => {"food": 4}
    verify_yields("Bath base yields",
                  {"food": 4},
                  yields_bath["base_yields"])

    # adjacency => +1 food from coastal_tile
    verify_yields("Bath adjacency yields",
                  {"food": 1},
                  yields_bath["adjacency_yields"])

    # quarter synergy => check if 'bath' or 'garden' have quarter_bonuses
    # According to your buildings.json, neither 'garden' nor 'bath'
    # list quarter_bonuses, so we expect 0. If you add some synergy, update here.
    verify_yields("Bath quarter yields",
                  {"food": 0},
                  yields_bath["quarter_yields"])

def test_optimizer_decisions():
    """
    Verify that the optimizer is making correct building placement decisions.
    We'll test with 'arena' because it has adjacency to mountain for +1 happiness.
    """
    print("\n=== Verifying Optimizer Decisions ===")

    city = CityLayout()
    optimizer = CityOptimizer(city)

    # Setup scenario
    city.set_tile_terrain(1, 0, "mountain", [], False)      # Non-buildable tile
    city.set_tile_terrain(1, 1, "plains_flat", [], False)   # Plains next to mountain
    city.set_tile_terrain(1, 2, "plains_flat", [], False)   # Plains not next to mountain
    city.set_tile_terrain(1, 3, "plains_flat", [], False)   # Another plains tile

    # Now run the single-building optimizer for 'arena' with happiness priority
    result = optimizer.optimize_building_placement("arena", {"happiness": 1.0})

    print("\nOptimizer 'arena' placement:")
    if result:
        print(f"Chosen position: Ring {result.position[0]}, Index {result.position[1]}")
        print(f"Total yields: {result.yields['total_yields']}")
    else:
        print("No placement found or skipping was chosen.")

    # Should NOT place the building on the mountain tile itself
    if result:
        assert result.position != (1, 0), "Should not place building on mountain (non-buildable)."

        # 'arena' base happiness=4, adjacency +1 if next to mountain => total 5
        assert result.yields['total_yields'].get('happiness', 0) == 5, (
            "Expected 5 happiness total (4 base + 1 adjacency)."
        )
