import json
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table

def load_game_data() -> Dict[str, Any]:
    """
    Loads the JSON file with building data. Adjust the path/filename
    if needed. For example, rename 'new_buildings.json' to match your file.
    """
    data_dir = Path(__file__).parent / 'data'
    json_file = data_dir / 'buildings.json'  # Or whatever your filename is
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {json_file.name}: {e}")
        return {}

def format_yields(yields_dict: Dict) -> str:
    """Format yields dictionary into a readable string."""
    if not yields_dict:
        return "None"
    return ", ".join(f"{k}: {v}" for k, v in yields_dict.items())

def format_list(items: List) -> str:
    """Format list into a readable string."""
    if not items:
        return "None"
    return ", ".join(str(i) for i in items)

def format_requirements(reqs: Dict) -> str:
    """
    Format placement requirements into a readable string.
    Adjust keys as needed for your JSON structure.
    """
    if not reqs:
        return "None"
    parts = []
    if 'tile_type' in reqs:
        parts.append(f"Tile type: {', '.join(reqs['tile_type'])}")
    if 'adjacent_to' in reqs:
        parts.append(f"Adjacent to: {', '.join(reqs['adjacent_to'])}")
    return " | ".join(parts) if parts else "None"

def format_adjacency_rules(rules_list: List[Dict]) -> str:
    """
    Format adjacency rules (list of dicts) into a readable string:
    [{
      "sources": [...],
      "bonus_yields": {...}
    }, ...]
    """
    if not rules_list:
        return "None"
    formatted = []
    for rule in rules_list:
        sources = rule.get("sources", [])
        bonus_yields = rule.get("bonus_yields", {})
        sources_str = ", ".join(sources) if sources else "None"
        yields_str = format_yields(bonus_yields)
        formatted.append(f"{sources_str} -> {yields_str}")
    return " | ".join(formatted)

def format_tile_bonuses(tile_bonuses_list: List[Dict]) -> str:
    """
    Format tile bonuses (list of dicts) into a readable string:
    [{
      "tile_type": "camp",
      "yields": { ... }
    }, ...]
    """
    if not tile_bonuses_list:
        return "None"
    formatted = []
    for tb in tile_bonuses_list:
        tile_type = tb.get("tile_type", "Unknown tile")
        yields_str = format_yields(tb.get("yields", {}))
        formatted.append(f"{tile_type} -> {yields_str}")
    return " | ".join(formatted)

def display_buildings_table() -> None:
    """Display all buildings from the loaded JSON in a formatted table."""
    data = load_game_data()
    if not data:
        print("No building data found.")
        return

    console = Console()
    table = Table(show_header=True, header_style="bold magenta", title="Buildings")

    # Define columns. Add or remove columns to match your data display needs.
    table.add_column("Building", style="cyan")
    table.add_column("Age", style="yellow")
    table.add_column("Category", style="blue")
    table.add_column("Yields", style="green")
    table.add_column("Placement Requirements", style="magenta")
    table.add_column("Costs", style="red")
    table.add_column("Adjacency Rules", style="cyan")
    table.add_column("Quarter Bonuses", style="yellow")
    table.add_column("Tile Bonuses", style="green")
    table.add_column("Special Rules", style="magenta")

    # data is a dict of { building_name: building_data }
    for building_name, building_data in sorted(data.items()):
        table.add_row(
            building_name,
            building_data.get('age', ''),
            building_data.get('category', ''),
            format_yields(building_data.get('yields', {})),
            format_requirements(building_data.get('placement_requirements', {})),
            format_yields(building_data.get('costs', {})),
            format_adjacency_rules(building_data.get('adjacency_rules', [])),
            format_yields(building_data.get('quarter_bonuses', {})),
            format_tile_bonuses(building_data.get('tile_bonuses', [])),
            format_list(building_data.get('special_rules', [])),
        )

    console.print(table)

if __name__ == "__main__":
    # For a simple CLI approach, just run the building table display.
    display_buildings_table()
