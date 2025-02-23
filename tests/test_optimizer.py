import pytest
from backend.city_layout import CityLayout
from backend.optimizer import CityOptimizer

@pytest.fixture
def city():
    return CityLayout()

@pytest.fixture
def optimizer(city):
    return CityOptimizer(city)

def test_basic_optimization(optimizer, city):
    """Test basic building placement optimization"""
    # Setup terrain for all positions we care about
    city.set_tile_terrain(0, 0, "plains_flat", [], False)  # Center
    city.set_tile_terrain(1, 0, "mountain", [], False)     # Mountain in ring 1
    city.set_tile_terrain(1, 1, "plains_flat", [], False)  # Plains adjacent to mountain
    city.set_tile_terrain(1, 2, "plains_flat", [], False)  # Plains not adjacent to mountain
    
    # Test with amphitheater (gets culture bonus from mountains)
    result = optimizer.optimize_building_placement(
        "amphitheater",
        yield_priorities={"culture": 1.0}
    )
    
    assert result is not None
    assert result.building == "amphitheater"
    # Should prefer position adjacent to mountain for culture bonus
    assert result.position == (1, 1)  # ring 1, adjacent to mountain
    assert result.yields['adjacency_yields']['culture'] > 0  # Should get mountain bonus

def test_multiple_building_optimization(optimizer, city):
    """Test optimizing placement of multiple buildings"""
    # Setup terrain for testing - only coastal tiles in ring 1
    city.set_tile_terrain(0, 0, "plains_flat", [], True)  # Center
    city.set_tile_terrain(1, 0, "coast", [], True)
    city.set_tile_terrain(1, 1, "coast", [], True)
    city.set_tile_terrain(1, 2, "plains_flat", [], True)
    
    # Try to place multiple buildings
    buildings = ["market", "bank"]  # These should work well together
    results = optimizer.optimize_multiple_buildings(
        buildings,
        yield_priorities={"gold": 1.0}
    )
    
    assert len(results) == 2
    assert results[0].building == "market"
    assert results[1].building == "bank"
    # Buildings should be placed on coastal tiles in ring 1
    assert all(r.position[0] == 1 and r.position[1] in [0, 1] for r in results)

def test_optimization_with_invalid_building(optimizer):
    """Test optimization with nonexistent building"""
    result = optimizer.optimize_building_placement("nonexistent_building")
    assert result is None

def test_yield_priorities(optimizer, city):
    """Test that yield priorities affect building placement"""
    # Setup mixed terrain
    city.set_tile_terrain(0, 0, "plains_flat", [], True)  # Center
    city.set_tile_terrain(1, 0, "coast", [], True)        # Coastal tile
    city.set_tile_terrain(1, 1, "plains_flat", [], True)  # Land tile
    
    # Test with different priorities
    result_gold = optimizer.optimize_building_placement(
        "market",
        yield_priorities={"gold": 1.0, "food": 0.0}
    )
    
    result_food = optimizer.optimize_building_placement(
        "market",
        yield_priorities={"gold": 0.0, "food": 1.0}
    )
    
    # Should get different scores based on priorities
    assert result_gold.score != result_food.score