import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from backend.city_layout import CityLayout
from backend.terrain_mapping import get_terrain_from_color, get_color_from_terrain

class LayoutStorage:
    def __init__(self, storage_dir: str = "saved_layouts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
    def save_layout(self, hex_data: Dict[str, str], name: Optional[str] = None) -> str:
        """
        Save a layout to disk.
        hex_data: Dictionary mapping hex positions to colors
        name: Optional name for the layout
        Returns: Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = name or f"layout_{timestamp}"
        filename = f"{name}.json"
        
        # Convert colors to terrain types
        terrain_data = {
            pos: get_terrain_from_color(color)
            for pos, color in hex_data.items()
        }
        
        # Save data with metadata
        data = {
            "name": name,
            "timestamp": timestamp,
            "terrain": terrain_data
        }
        
        with open(self.storage_dir / filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        return filename
    
    def load_layout(self, filename: str) -> Dict[str, str]:
        """
        Load a layout from disk.
        Returns: Dictionary mapping hex positions to colors
        """
        try:
            with open(self.storage_dir / filename, 'r') as f:
                data = json.load(f)
                
            # Convert terrain types back to colors
            return {
                pos: get_color_from_terrain(terrain)
                for pos, terrain in data["terrain"].items()
            }
        except Exception as e:
            print(f"Error loading layout {filename}: {e}")
            return {}
            
    def list_layouts(self) -> List[Dict]:
        """List all saved layouts with metadata"""
        layouts = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                layouts.append({
                    "filename": path.name,
                    "name": data.get("name", path.stem),
                    "timestamp": data.get("timestamp", "")
                })
            except Exception as e:
                print(f"Error reading {path}: {e}")
        return sorted(layouts, key=lambda x: x["timestamp"], reverse=True)
    
    def create_city_layout(self, hex_data: Dict[str, str]) -> CityLayout:
        """Convert hex data to CityLayout object"""
        city = CityLayout()
        
        for pos, color in hex_data.items():
            # Parse position string "(ring,index)"
            ring, index = map(int, pos.strip("()").split(","))
            terrain = get_terrain_from_color(color)
            if terrain:
                # For now, we're not setting features or fresh water
                city.set_tile_terrain(ring, index, terrain, [], False)
                
        return city