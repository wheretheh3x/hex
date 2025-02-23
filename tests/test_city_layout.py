import pytest
from backend.city_layout import CityLayout

def test_grid_initialization():
    """Test that the grid is initialized with correct number of tiles."""
    city = CityLayout()
    # Center tile
    assert city.get_tile(0, 0) is not None
    # First ring (6 tiles)
    for i in range(6):
        assert city.get_tile(1, i) is not None
    # Second ring (12 tiles)
    for i in range(12):
        assert city.get_tile(2, i) is not None
    # Third ring (18 tiles)
    for i in range(18):
        assert city.get_tile(3, i) is not None

def test_terrain_setting():
    """Test setting terrain for tiles."""
    city = CityLayout()
    city.set_tile_terrain(1, 0, "plains_flat", ["forest"], True)
    tile = city.get_tile(1, 0)
    assert tile.terrain_type == "plains_flat"
    assert tile.features == ["forest"]
    assert tile.has_fresh_water == True

def test_building_placement():
    """Test adding buildings to tiles."""
    city = CityLayout()
    # Set appropriate terrain for water buildings
    city.set_tile_terrain(1, 0, "coast", [], True)
    # Add first building
    success = city.add_building(1, 0, "market")
    assert success == True
    tile = city.get_tile(1, 0)
    assert "market" in tile.buildings
    # Add second building to same tile
    success = city.add_building(1, 0, "bank")
    assert success == True
    assert len(tile.buildings) == 2
    # Try to add third building (should fail)
    success = city.add_building(1, 0, "granary")
    assert success == False
    assert len(tile.buildings) == 2

def test_adjacency_calculation():
    """Test getting adjacent tiles."""
    city = CityLayout()
    # Test center tile adjacencies (should have 6 adjacent tiles)
    center_adjacents = city.get_adjacent_positions(0, 0)
    assert len(center_adjacents) == 6
    for pos in center_adjacents:
        assert pos[0] == 1  # all should be in first ring

def test_tile_retrieval():
    """Test getting tiles at various positions."""
    city = CityLayout()
    # Valid positions
    assert city.get_tile(0, 0) is not None  # Center
    assert city.get_tile(1, 0) is not None  # First ring
    assert city.get_tile(2, 0) is not None  # Second ring
    assert city.get_tile(3, 0) is not None  # Third ring
    # Invalid positions
    assert city.get_tile(4, 0) is None  # Outside grid
    assert city.get_tile(-1, 0) is None  # Invalid ring

def test_adjacency_patterns():
    """Test specific adjacency patterns."""
    city = CityLayout()
    # First ring tile should be adjacent to:
    # - Center (1 tile)
    # - Two other first ring tiles
    # - Three second ring tiles
    adjacents = city.get_adjacent_positions(1, 0)
    assert len(adjacents) == 6
    assert (0, 0) in adjacents  # Center
    assert sum(1 for pos in adjacents if pos[0] == 1) == 2  # First ring
    assert sum(1 for pos in adjacents if pos[0] == 2) == 3  # Second ring

def test_building_validation():
    """Test building placement validation."""
    city = CityLayout()
    # Set appropriate terrain
    city.set_tile_terrain(1, 0, "coast", [], True)
    # Try to place buildings
    assert city.is_valid_building_location(1, 0, "market") == True
    assert city.is_valid_building_location(1, 0, "nonexistent_building") == False