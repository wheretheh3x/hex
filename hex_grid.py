import math
import json
from flask import Flask, render_template_string

###############################################################################
# 1) Adjustable layout variables
###############################################################################
TILE_SIZE = 40.0             # Base radius of each hex
HEX_CORNER_ANGLE_OFFSET = 30.0  # 30 => pointy-top, 0 => flat-top

# For evenly spaced hexagons
HORIZONTAL_SPACING = TILE_SIZE * math.sqrt(3)  # Equal to 2 * TILE_SIZE * cos(30°)
VERTICAL_SPACING = TILE_SIZE * 1.5

###############################################################################
# 2) Functions to generate tile geometry
###############################################################################

def ring_center(r, i):
    """
    Compute (x,y) for tile (r,i).
    - r = ring # (0..3)
    - i = tile index within ring (0..6*r-1)
    
    Uses axial coordinates with conversion to cartesian for rendering.
    """
    if r == 0:
        # Center tile at (0,0)
        return (0.0, 0.0)

    # Determine which of the 6 sides this index falls on and position along that side
    side = i // r
    pos = i % r
    
    # Starting coordinates for each side
    # Using cube coordinates (q, r, s) where q + r + s = 0
    if side == 0:
        # Top-right edge
        q, r, s = r, -pos, -r+pos
    elif side == 1:
        # Right edge
        q, r, s = r-pos, -r, pos
    elif side == 2:
        # Bottom-right edge
        q, r, s = -pos, -r+pos, r
    elif side == 3:
        # Bottom-left edge
        q, r, s = -r, pos, r-pos
    elif side == 4:
        # Left edge
        q, r, s = -r+pos, r, -pos
    else:  # side == 5
        # Top-left edge
        q, r, s = pos, r-pos, -r
    
    # Convert axial to cartesian coordinates for rendering
    # For pointy-top hexagons:
    x = HORIZONTAL_SPACING * (q + s/2)
    y = VERTICAL_SPACING * s
    
    return (x, y)

def compute_hex_corners(cx, cy):
    """Return 6 corner points for a single hex at center (cx, cy)."""
    corners = []
    for k in range(6):
        angle_deg = HEX_CORNER_ANGLE_OFFSET + 60 * k
        rad = math.radians(angle_deg)
        xk = cx + TILE_SIZE * math.cos(rad)
        yk = cy + TILE_SIZE * math.sin(rad)
        corners.append((xk, yk))
    return corners

def generate_all_tiles(max_ring=3):
    """Build tile data for rings 0..max_ring."""
    tiles = []
    for r in range(max_ring + 1):
        if r == 0:
            # Center tile
            cx, cy = (0.0, 0.0)
            corners = compute_hex_corners(cx, cy)
            tiles.append({
                "ring": r,
                "index": 0,
                "label": "(0,0)",
                "center": (cx, cy),
                "corners": corners
            })
        else:
            n_tiles = 6 * r
            for i in range(n_tiles):
                cx, cy = ring_center(r, i)
                corners = compute_hex_corners(cx, cy)
                tiles.append({
                    "ring": r,
                    "index": i,
                    "label": f"({r},{i})",
                    "center": (cx, cy),
                    "corners": corners
                })
    return tiles


###############################################################################
# 3) Build the SVG for the layout
###############################################################################

def build_svg(tiles, svg_size=600):
    """Build the SVG for the hexagonal grid."""
    allx = []
    ally = []
    for tile in tiles:
        for (px, py) in tile["corners"]:
            allx.append(px)
            ally.append(py)

    min_x, max_x = min(allx), max(allx)
    min_y, max_y = min(ally), max(ally)
    width_x = max_x - min_x
    height_y = max_y - min_y

    margin = 5
    scale = (svg_size - 2*margin) / max(width_x, height_y)

    # ring color
    ring_colors = {
        0: "#333333",
        1: "#444444",
        2: "#555555",
        3: "#666666"
    }

    # yield text background colors
    yield_colors = {
        "food": "#00FF00",
        "gold": "gold",
        "science": "#0000FF",
        "production": "#8B4513",
        "culture": "#800080",
        "happiness": "#FF8C00",
        "influence": "#708090"
    }

    # layout: 7 yields in 2 rows
    yield_positions = [
        ("food",       -30,  +25),
        ("gold",       -10,  +25),
        ("science",    +10,  +25),
        ("production", +30,  +25),
        ("culture",    -20,  +35),
        ("happiness",    0,  +35),
        ("influence",  +20,  +35)
    ]

    svg = [f'<svg id="hex-svg" width="{svg_size}" height="{svg_size}" '
           f'viewBox="0 0 {svg_size} {svg_size}" '
           f'style="background-color:#000;" xmlns="http://www.w3.org/2000/svg">']

    for tile in tiles:
        r = tile["ring"]
        lbl = tile["label"]
        cx, cy = tile["center"]

        # transform corners for this tile
        poly_pts = []
        for (px, py) in tile["corners"]:
            sx = (px - min_x)*scale + margin
            sy = (max_y - py)*scale + margin
            poly_pts.append(f"{sx},{sy}")
        pts_str = " ".join(poly_pts)

        # tile center in the scaled SVG space
        center_sx = (cx - min_x)*scale + margin
        center_sy = (max_y - cy)*scale + margin

        default_fill = ring_colors.get(r, "#666666")

        # data-cx, data-cy store the SVG center so we can place text backgrounds
        svg.append(
            f'<g class="tile-group" data-ring="{r}" data-label="{lbl}" '
            f'data-cx="{center_sx}" data-cy="{center_sy}">'
        )
        svg.append(
            f'  <polygon class="hex" fill="{default_fill}" '
            f'       data-ring="{r}" data-label="{lbl}" '
            f'       points="{pts_str}" style="stroke:#999; stroke-width:1; cursor:pointer;" />'
        )

        # yields (14 x 12 rects)
        for (ytype, dx, dy) in yield_positions:
            rx = center_sx + dx - 7
            ry = center_sy + dy - 6
            color_for_yield = yield_colors.get(ytype, "#888")
            svg.append(
                f'  <rect class="yield-bg yield-bg-{ytype}" '
                f'       x="{rx}" y="{ry}" width="14" height="12" '
                f'       fill="{color_for_yield}" style="display:none;" />'
            )
            tx = center_sx + dx
            ty = center_sy + dy
            svg.append(
                f'  <text class="yield-slot yield-{ytype}" data-ytype="{ytype}" '
                f'        text-anchor="middle" x="{tx}" y="{ty}" '
                f'        font-size="9" fill="#ffffff" style="display:none;">+1</text>'
            )
        svg.append('</g>')
    svg.append('</svg>')
    return "\n".join(svg)


###############################################################################
# 4) Data for terrain and buildings
###############################################################################

def get_excel_grid_data():
    """Full data for terrain & buildings based on the provided image."""
    return [
        # Row 1 - Deserts and Tropics
        [
            {"label": "DESERT<br>ROUGH", "bg": "#C66300", "isBuilding": False, "actionKey": "#C66300"},
            {"label": "DESERT<br>FLAT", "bg": "#D68023", "isBuilding": False, "actionKey": "#D68023"},
            {"label": "WET<br>(OASIS)", "bg": "#C8A03A", "isBuilding": False, "actionKey": "#C8A03A"},
            {"label": "VEGETATED<br>(STEPPE)", "bg": "#E99C2E", "isBuilding": False, "actionKey": "#E99C2E"},
            {"label": "TROPICAL<br>ROUGH", "bg": "#D46A00", "isBuilding": False, "actionKey": "#D46A00"},
            {"label": "TROPICAL<br>FLAT", "bg": "#EB7E23", "isBuilding": False, "actionKey": "#EB7E23"},
            {"label": "WET<br>(MANGROVE)", "bg": "#4CAF50", "isBuilding": False, "actionKey": "#4CAF50"},
            {"label": "VEGETATED<br>(RAINFORST)", "bg": "#2F6F2F", "isBuilding": False, "actionKey": "#2F6F2F"},
        ],
        # Row 2 - Tundra and Grasslands
        [
            {"label": "TUNDRA<br>ROUGH", "bg": "#666666", "isBuilding": False, "actionKey": "#666666"},
            {"label": "TUNDRA<br>FLAT", "bg": "#999999", "isBuilding": False, "actionKey": "#999999"},
            {"label": "WET<br>(BOG)", "bg": "#444444", "isBuilding": False, "actionKey": "#444444"},
            {"label": "VEGETATED<br>(TAIGA)", "bg": "#556B2F", "isBuilding": False, "actionKey": "#556B2F"},
            {"label": "GRASSLAND<br>ROUGH", "bg": "#38761D", "isBuilding": False, "actionKey": "#38761D"},
            {"label": "GRASSLAND<br>FLAT", "bg": "#4AA52E", "isBuilding": False, "actionKey": "#4AA52E"},
            {"label": "WET<br>(MARSH)", "bg": "#507F60", "isBuilding": False, "actionKey": "#507F60"},
            {"label": "VEGETATED<br>(FOREST)", "bg": "#2E5808", "isBuilding": False, "actionKey": "#2E5808"},
        ],
        # Row 3 - Plains and Water
        [
            {"label": "PLAINS<br>ROUGH", "bg": "#D47F60", "isBuilding": False, "actionKey": "#D47F60"},
            {"label": "PLAINS<br>FLAT", "bg": "#F2AC83", "isBuilding": False, "actionKey": "#F2AC83"},
            {"label": "WET<br>(WATERING)", "bg": "#EEB36D", "isBuilding": False, "actionKey": "#EEB36D"},
            {"label": "VEGETATED<br>(SAVANNA)", "bg": "#F0AE50", "isBuilding": False, "actionKey": "#F0AE50"},
            {"label": "OPEN<br>OCEAN", "bg": "#1E90FF", "isBuilding": False, "actionKey": "#1E90FF"},
            {"label": "COASTAL", "bg": "#66B3FF", "isBuilding": False, "actionKey": "#66B3FF"},
            {"label": "COASTAL<br>LAKE", "bg": "#99CEFF", "isBuilding": False, "actionKey": "#99CEFF"},
            {"label": "NAVIGABLE<br>RIVER", "bg": "#4682B4", "isBuilding": False, "actionKey": "#4682B4"},
        ],
        # Row 4 - Special Features
        [
            {"label": "NATURAL<br>WONDER", "bg": "#CCCC00", "isBuilding": False, "actionKey": "#CCCC00"},
            {"label": "MOUNTAIN", "bg": "#003366", "isBuilding": False, "actionKey": "#003366"},
            {"label": "VOLCANO", "bg": "#FF4500", "isBuilding": False, "actionKey": "#FF4500"},
            {"label": "MINOR<br>RIVER", "bg": "#00AAAA", "isBuilding": False, "actionKey": "#00AAAA"},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
        ],
        # Row 5 - Buildings: Food Production
        [
            {"label": "GRANARY", "bg": "#222222", "textColor": "#00AA00", "isBuilding": True, "actionKey": "granary"},
            {"label": "FISHING<br>QUAY", "bg": "#222222", "textColor": "#00AA00", "isBuilding": True, "actionKey": "fishing_quay"},
            {"label": "SAW PIT", "bg": "#222222", "textColor": "#FF6600", "isBuilding": True, "actionKey": "saw_pit"},
            {"label": "BRICKYARD", "bg": "#222222", "textColor": "#FF6600", "isBuilding": True, "actionKey": "brickyard"},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
        ],
        # Row 6 - More Buildings
        [
            {"label": "GARDEN", "bg": "#222222", "textColor": "#00AA00", "isBuilding": True, "actionKey": "garden"},
            {"label": "BATH", "bg": "#222222", "textColor": "#00AA00", "isBuilding": True, "actionKey": "bath"},
            {"label": "MARKET", "bg": "#222222", "textColor": "#FFBB00", "isBuilding": True, "actionKey": "market"},
            {"label": "LIGHTHOUSE", "bg": "#222222", "textColor": "#FFBB00", "isBuilding": True, "actionKey": "lighthouse"},
            {"label": "ANCIENT<br>BRIDGE", "bg": "#222222", "textColor": "#FFBB00", "isBuilding": True, "actionKey": "ancient_bridge"},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
        ],
        # Row 7 - Science and Military Buildings
        [
            {"label": "LIBRARY", "bg": "#222222", "textColor": "#6699FF", "isBuilding": True, "actionKey": "library"},
            {"label": "ACADEMY", "bg": "#222222", "textColor": "#6699FF", "isBuilding": True, "actionKey": "academy"},
            {"label": "BARRACKS", "bg": "#222222", "textColor": "#FF6600", "isBuilding": True, "actionKey": "barracks"},
            {"label": "BLACKSMITH", "bg": "#222222", "textColor": "#FF6600", "isBuilding": True, "actionKey": "blacksmith"},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
        ],
        # Row 8 - Culture and Entertainment Buildings
        [
            {"label": "MONUMENT", "bg": "#222222", "textColor": "#CC66FF", "isBuilding": True, "actionKey": "monument"},
            {"label": "AMPHI<br>THEATRE", "bg": "#222222", "textColor": "#CC66FF", "isBuilding": True, "actionKey": "amphitheatre"},
            {"label": "ALTAR", "bg": "#222222", "textColor": "#FF6600", "isBuilding": True, "actionKey": "altar"},
            {"label": "VILLA", "bg": "#222222", "textColor": "#FF6600", "isBuilding": True, "actionKey": "villa"},
            {"label": "ARENA", "bg": "#222222", "textColor": "#FF6600", "isBuilding": True, "actionKey": "arena"},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "textColor": "#FFFFFF", "isBuilding": False, "actionKey": ""},
        ],
    ]

def build_excel_layout_html():
    rows = get_excel_grid_data()
    html = ['<div class="excel-grid" style="padding:10px; display:table;">']
    for row in rows:
        html.append('<div class="excel-row" style="display:table-row;">')
        for cell in row:
            label = cell["label"]
            bg_color = cell["bg"]
            is_bldg = cell["isBuilding"]
            key = cell["actionKey"]
            text_color = cell.get("textColor", "#FFFFFF")
            
            onclick = ""
            if is_bldg:
                onclick = f"selectBuilding('{key}')"
            else:
                if key and key != "#000000":
                    onclick = f"setColor('{key}', this)"

            cell_html = f'''
            <div class="excel-cell"
                 style="display:table-cell; vertical-align:middle;
                        cursor:pointer; border:1px solid #333;
                        text-align:center; padding:4px;
                        min-width:60px; min-height:60px;
                        background-color:{bg_color};
                        color:{text_color};"
                 onclick="{onclick}">
              {label}
            </div>
            '''
            html.append(cell_html)
        html.append('</div>')
    html.append('</div>')
    return "\n".join(html)


###############################################################################
# 5) HTML template and Flask app
###############################################################################

# HTML template as a separate string
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
  <title>Hex City Planner</title>
  <style>
    html, body {
      margin: 0; 
      padding: 0; 
      width: 100%;
      height: 100%;
      background-color:#000;
      color:#AAA;
      font-family: "Courier New", monospace;
      font-size:14px;
      overflow: hidden;
    }
    .container {
      display: flex;
      width: 100%;
      height: 100%;
      flex-direction: row;
    }
    .drag-bar {
      width: 5px;
      background:#666;
      cursor: col-resize;
      position: relative;
      z-index: 999;
    }
    .left-panel {
      background-color: #000;
      height: 100%;
      flex: 0 0 50%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      position: relative;
      overflow: hidden;
    }
    .right-panel {
      flex: 1;
      background-color: #000;
      overflow-y: auto;
      border-left:1px solid #666;
      box-sizing: border-box;
      padding-bottom:60px;
    }
    #hex-svg {
      display: block;
      margin: 0 auto;
    }
    .action-bar {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 10px;
      margin:10px 0;
    }
    .action-btn {
      width:100px;
      height:48px;
      background:#444;
      color:#FFF;
      font-size:0.9em;
      border:1px solid #666;
      border-radius:4px;
      cursor:pointer;
      text-transform:uppercase;
      line-height:1.2em;
      white-space: nowrap;
      overflow: hidden;
    }
    .action-btn:hover {
      background:#555;
    }
    #status-msg {
      position:absolute; 
      bottom:10px; 
      left:50%; 
      transform:translateX(-50%);
      background:#222;
      color:#EEE;
      padding:6px 10px;
      border-radius:4px;
      opacity:0;
      transition:opacity 1s;
      pointer-events:none;
      z-index:9999;
    }
    .excel-cell {
      font-size: 12px;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <div class="container">
    <div id="left-panel" class="left-panel">
      {{ svg_code|safe }}
      {{ actions_html|safe }}
    </div>
    <div id="drag-bar" class="drag-bar"></div>
    <div class="right-panel">
      {{ excel_html|safe }}
    </div>
  </div>
  <div id="status-msg"></div>

  <script>
    // Building colors for displaying buildings on hexes
    var buildingColors = {{ building_colors|safe }};
    var currentLayout = {};
    var currentBuildings = {};
    var buildingToTile = {};

    var selectedColor = null;
    var selectedBuilding = null;
    var lastActions = [];
    var statusTimer = null;
    var isPainting=false;

    function setColor(col, btn) {
      selectedColor = col;
      selectedBuilding = null;
      showStatus("Selected color: "+col);
    }
    function selectBuilding(bldg) {
      selectedBuilding = bldg;
      selectedColor = null;
      showStatus("Selected building: "+bldg.toUpperCase());
    }
    function onHexClick(evt) {
      var hex = evt.target;
      if(!hex.classList.contains("hex")) return;
      var tile = hex.getAttribute("data-label");
      if(selectedBuilding) {
        placeBuilding(tile, selectedBuilding);
      } 
      else if(selectedColor) {
        paintTile(tile, hex, selectedColor);
      }
    }
    function paintTile(tile, hex, color) {
      lastActions.push({
        type:"terrain", tile:tile, oldFill:hex.getAttribute("fill"), element:hex
      });
      hex.setAttribute("fill", color);
      currentLayout[tile] = color;
      showYields(tile);
    }
    function placeBuilding(tile, bldg) {
      if(buildingToTile[bldg]) {
        var oldTile = buildingToTile[bldg];
        var arr = currentBuildings[oldTile];
        if(arr) {
          var idx = arr.indexOf(bldg);
          if(idx>=0) {
            arr.splice(idx,1);
            updateBuildingText(oldTile);
            showYields(oldTile);
          }
        }
      }
      if(!currentBuildings[tile]) currentBuildings[tile] = [];
      var arr2 = currentBuildings[tile];
      if(arr2.length>=2) {
        showStatus(tile+" already has 2 buildings!");
        return;
      }
      if(arr2.length==1) {
        var existing = arr2[0];
        if(bldg.length>existing.length) {
          arr2[0] = bldg;
          arr2.push(existing);
        } else {
          arr2.push(bldg);
        }
      } else {
        arr2.push(bldg);
      }
      buildingToTile[bldg] = tile;
      lastActions.push({type:"building", tile:tile, building:bldg});
      showStatus("Placed "+bldg.toUpperCase()+" in "+tile);
      updateBuildingText(tile);
      showYields(tile);
    }

    function updateBuildingText(tile) {
      var group = document.querySelector('.tile-group[data-label="'+tile+'"]');
      if(!group) return;
      var arr = currentBuildings[tile] || [];

      let oldBgs = group.querySelectorAll(".bld-bg-dynamic");
      oldBgs.forEach(bg => bg.remove());
      let oldTexts = group.querySelectorAll(".bld-slot-dynamic");
      oldTexts.forEach(t => t.remove());

      if(arr.length===0) return;

      let cx = parseFloat(group.getAttribute("data-cx"));
      let cy = parseFloat(group.getAttribute("data-cy"));

      // building #1 text near (cx, cy-10), #2 near (cx, cy-20), etc
      arr.forEach((bldName, idx) => {
        let yOffset = -10 - (idx*10);

        let txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
        txt.setAttribute("class", "bld-slot-dynamic");
        txt.setAttribute("x", cx.toString());
        txt.setAttribute("y", (cy + yOffset).toString());
        txt.setAttribute("text-anchor", "middle");
        txt.setAttribute("font-size", "9");
        let color = buildingColors[bldName] || "#ffffff";
        txt.setAttribute("fill", color);
        txt.textContent = bldName.toUpperCase();
        group.appendChild(txt);

        let bbox = txt.getBBox();
        let padX = 3;
        let padY = 2;
        let w = bbox.width + padX*2;
        let h = bbox.height + padY*2;
        let rectX = bbox.x - padX;
        let rectY = bbox.y - padY;

        let bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        bg.setAttribute("class", "bld-bg-dynamic");
        bg.setAttribute("x", rectX.toString());
        bg.setAttribute("y", rectY.toString());
        bg.setAttribute("width", w.toString());
        bg.setAttribute("height", h.toString());
        bg.setAttribute("fill", "#333333");
        group.insertBefore(bg, txt);
      });
    }

    function showYields(tile) {
      var group = document.querySelector('.tile-group[data-label="'+tile+'"]');
      if(!group) return;
      var hasTerrain = currentLayout[tile];
      var hasBldg = (currentBuildings[tile] && currentBuildings[tile].length>0);
      var showIt = (hasTerrain||hasBldg);
      var yieldSlots = group.querySelectorAll(".yield-slot");
      var yieldBgs   = group.querySelectorAll(".yield-bg");
      yieldSlots.forEach(function(e){ e.style.display=showIt?"block":"none"; });
      yieldBgs.forEach(function(e){ e.style.display=showIt?"block":"none"; });

      if(!showIt) return;
      yieldSlots.forEach(function(e){
        var val = Math.floor(1+Math.random()*15);
        e.textContent = "+" + val;
      });
    }

    function undo() {
      if(!lastActions.length)return;
      var action = lastActions.pop();
      if(action.type=="terrain") {
        action.element.setAttribute("fill", action.oldFill);
        delete currentLayout[action.tile];
        showYields(action.tile);
      } else if(action.type=="building") {
        var arr = currentBuildings[action.tile];
        if(arr) {
          var idx = arr.indexOf(action.building);
          if(idx>=0) arr.splice(idx,1);
          if(buildingToTile[action.building]==action.tile) delete buildingToTile[action.building];
          updateBuildingText(action.tile);
          showYields(action.tile);
        }
      }
    }
    function clearAll() {
      currentLayout={};
      currentBuildings={};
      buildingToTile={};
      var hexes = document.querySelectorAll(".hex");
      hexes.forEach(function(h){
        var r = parseInt(h.getAttribute("data-ring"));
        var col = "#666666";
        if(r==0) col="#333333";
        if(r==1) col="#444444";
        if(r==2) col="#555555";
        if(r==3) col="#666666";
        h.setAttribute("fill", col);
      });
      var groups = document.querySelectorAll(".tile-group");
      groups.forEach(function(g){
        var tile = g.getAttribute("data-label");
        updateBuildingText(tile);
        showYields(tile);
      });
      showStatus("Everything cleared");
    }
    function saveLayout() {
      showStatus("Save layout not fully implemented");
    }
    function applyAll() {
      if(!selectedColor)return;
      var hexes = document.querySelectorAll(".hex");
      hexes.forEach(function(h){
        var tile = h.getAttribute("data-label");
        lastActions.push({
          type:"terrain", tile:tile, oldFill:h.getAttribute("fill"), element:h
        });
        h.setAttribute("fill", selectedColor);
        currentLayout[tile]=selectedColor;
        showYields(tile);
      });
      showStatus("Applied color to all tiles");
    }
    function calcYield() {
      showStatus("Yield calc not implemented here");
    }
    function reportAction() {
      showStatus("Reporting not implemented");
    }
    function showStatus(msg) {
      var st = document.getElementById("status-msg");
      st.textContent = msg;
      st.style.opacity=1;
      if(statusTimer) clearTimeout(statusTimer);
      statusTimer=setTimeout(function(){
        st.style.opacity=0;
      },2000);
    }
    
    // DRAG-PAINT
    document.addEventListener("mousedown", function(e){
      if(selectedColor) {
        isPainting=true;
        e.preventDefault();
      }
    });
    document.addEventListener("mouseup", function(e){
      isPainting=false;
    });
    document.addEventListener("mousemove", function(e){
      if(!isPainting||!selectedColor)return;
      e.preventDefault();
      var el = document.elementFromPoint(e.clientX, e.clientY);
      if(el && el.classList.contains("hex")){
        var tile = el.getAttribute("data-label");
        paintTile(tile, el, selectedColor);
      }
    });

    window.onload=function(){
      var hexes = document.querySelectorAll(".hex");
      hexes.forEach(function(h){
        h.addEventListener("mousedown", onHexClick);
      });

      // The drag bar for resizing
      const dragBar = document.getElementById("drag-bar");
      const leftPanel = document.getElementById("left-panel");
      let dragging = false;
      dragBar.addEventListener("mousedown", function(e){
        dragging = true;
        e.preventDefault();
      });
      document.addEventListener("mousemove", function(e){
        if(!dragging) return;
        let totalWidth = document.body.clientWidth;
        let newWidth = e.clientX;
        if(newWidth < 100) newWidth=100;
        if(newWidth > totalWidth-100) newWidth = totalWidth-100;
        leftPanel.style.flex = "0 0 " + newWidth + "px";
      });
      document.addEventListener("mouseup", function(e){
        dragging = false;
      });
    };
  </script>
</body>
</html>
'''

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def main_route():
    # Generate tile geometry
    tiles = generate_all_tiles(max_ring=3)
    
    # Build the main SVG
    svg_code = build_svg(tiles, 600)
    
    # Build the palette layout
    excel_html = build_excel_layout_html()
    
    # Action buttons HTML
    actions_html = '''
    <div class="action-bar">
      <button class="action-btn" onclick="undo()">UNDO</button>
      <button class="action-btn" onclick="clearAll()">CLEAR</button>
      <button class="action-btn" onclick="saveLayout()">SAVE</button>
      <button class="action-btn" onclick="applyAll()">APPLY ALL</button>
      <button class="action-btn" onclick="calcYield()">CALC YIELD</button>
      <button class="action-btn" onclick="reportAction()">REPORT</button>
    </div>
    '''
    
    # Building colors - complete set from image
    building_colors = {
      "monument": "#CC66FF",
      "amphitheatre": "#CC66FF",
      "library": "#6699FF",
      "academy": "#6699FF",
      "granary": "#00AA00",
      "fishing_quay": "#00AA00",
      "garden": "#00AA00",
      "bath": "#00AA00",
      "market": "#FFBB00",
      "lighthouse": "#FFBB00",
      "ancient_bridge": "#FFBB00",
      "saw_pit": "#FF6600",
      "brickyard": "#FF6600",
      "barracks": "#FF6600",
      "blacksmith": "#FF6600",
      "altar": "#FF6600",
      "villa": "#FF6600",
      "arena": "#FF6600"
    }
    
    # Render the template with all our data
    return render_template_string(
        HTML_TEMPLATE,
        svg_code=svg_code,
        excel_html=excel_html,
        actions_html=actions_html,
        building_colors=json.dumps(building_colors)
    )

# Run the application with specific host and port settings
if __name__ == "__main__":
    # Use 0.0.0.0 to make it externally visible
    # Print clear instructions
    print("\n==== Hex Grid App ====")
    print("Starting server at http://127.0.0.1:5000")
    print("If that doesn't work, try: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("======================\n")
    
    # Run with debug on for enhanced development experience
    app.run(host='0.0.0.0', port=5000, debug=True)