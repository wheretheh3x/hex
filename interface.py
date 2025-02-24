import math
from flask import Flask

#
# --- HEX MAP LOGIC (with ring 3 fix) ---
#

def base_hex_center(r, i, size):
    if r == 0:
        return (0.0, 0.0)
    num = 6 * r
    ang = math.radians(90 - (i - 1) * (360 / num))
    return (math.sqrt(3) * r * size * math.cos(ang),
            math.sqrt(3) * r * size * math.sin(ang))

def final_ring2_center(i, size):
    x, y = base_hex_center(2, i, size)
    if i % 2 == 0:
        ang = math.radians(90 - (i - 1) * (360 / 12))
        r0 = math.sqrt(3) * 2 * size
        r_new = r0 - 0.45 * size
        x, y = r_new * math.cos(ang), r_new * math.sin(ang)
    return (x, y)

ANCHORS_3 = [1, 4, 7, 10, 13, 16]

def ring3_interpolated_center(i, size):
    # BUG FIX: changed second coordinate from yB + frac*(yB - yA)
    # to yA + frac*(yB - yA)
    if i in ANCHORS_3:
        return base_hex_center(3, i, size)
    sorted_a = sorted(ANCHORS_3)
    if any(a > i for a in sorted_a):
        anchorB = min(a for a in sorted_a if a > i)
        anchorA = max(a for a in sorted_a if a <= i)
    else:
        anchorB, anchorA = sorted_a[0], sorted_a[-1]
    xA, yA = base_hex_center(3, anchorA, size)
    xB, yB = base_hex_center(3, anchorB, size)
    distAB = (anchorB - anchorA) if (anchorB > anchorA) else (anchorB - anchorA + 18)
    distAi = (i - anchorA) if i >= anchorA else (i - anchorA + 18)
    frac = distAi / distAB
    return (
        xA + frac * (xB - xA),
        yA + frac * (yB - yA)   # <-- FIXED HERE
    )

def final_ring3_center(i, size):
    return ring3_interpolated_center(i, size)

def get_tile_center(r, i, size):
    if r == 0:
        return (0.0, 0.0)
    if r == 1:
        return base_hex_center(1, i, size)
    if r == 2:
        return final_ring2_center(i, size)
    if r == 3:
        return final_ring3_center(i, size)
    return (0.0, 0.0)

def flat_topped_hex_corners(cx, cy, size):
    return [
        (
            cx + size * math.cos(math.radians(60 * k)),
            cy + size * math.sin(math.radians(60 * k))
        )
        for k in range(6)
    ]

def generate_all_tiles(max_ring=3, size=1.0):
    tiles = []
    for r in range(max_ring + 1):
        if r == 0:
            cx, cy = get_tile_center(0, 1, size)
            corners = flat_topped_hex_corners(cx, cy, size * 0.95)
            tiles.append({'label': "(0,0)", 'ring': 0, 'index': 0, 'corners': corners})
        else:
            for i in range(1, 6 * r + 1):
                cx, cy = get_tile_center(r, i, size)
                corners = flat_topped_hex_corners(cx, cy, size * 0.95)
                tiles.append({'label': f"({r},{i-1})", 'ring': r, 'index': i-1, 'corners': corners})
    return tiles

def build_svg(tiles, svg_size=600):
    min_x = min(x for t in tiles for (x, _) in t['corners'])
    max_x = max(x for t in tiles for (x, _) in t['corners'])
    min_y = min(y for t in tiles for (_, y) in t['corners'])
    max_y = max(y for t in tiles for (_, y) in t['corners'])
    scale = (svg_size - 10) / max(max_x - min_x, max_y - min_y)

    # If you'd like different ring colors, tweak below:
    color_map = {
        0: '#333333',
        1: '#444444',
        2: '#555555',
        3: '#666666'
    }

    svg = [f'<svg id="hex-svg" width="{svg_size}" height="{svg_size}" '
           f'viewBox="0 0 {svg_size} {svg_size}" xmlns="http://www.w3.org/2000/svg">']

    for t in tiles:
        pts = []
        for (x, y) in t['corners']:
            sx = (x - min_x) * scale + 5
            sy = (max_y - y) * scale + 5
            pts.append(f"{sx},{sy}")
        pts_str = " ".join(pts)
        col = color_map.get(t["ring"], "#666666")
        svg.append(
            f'<polygon class="hex" data-ring="{t["ring"]}" data-label="{t["label"]}" '
            f'fill="{col}" points="{pts_str}" '
            f'style="stroke:#999; stroke-width:1; cursor:pointer; transition: fill 0.3s ease;" />'
        )

    svg.append('</svg>')
    return "\n".join(svg)

#
# --- 8×8 GRID LAYOUT FROM YOUR EXCEL MOCKUP (with slight shift) ---
#

def get_excel_grid_data():
    """
    Returns the final 8x8 list-of-lists with each cell's text & color.
    Some color tweaks or label changes below as needed.
    """
    return [
        # Row 1
        [
            {"label": "DESERT\nROUGH", "bg": "#C66300", "isBuilding": False, "actionKey": "#C66300"},
            {"label": "DESERT\nFLAT",  "bg": "#D68023", "isBuilding": False, "actionKey": "#D68023"},
            {"label": "WET\n(OASIS)",  "bg": "#C8A03A", "isBuilding": False, "actionKey": "#C8A03A"},
            {"label": "VEGETATED\n(STEPPE)", "bg": "#E99C2E", "isBuilding": False, "actionKey": "#E99C2E"},
            {"label": "TROPICAL\nROUGH", "bg": "#D46A00", "isBuilding": False, "actionKey": "#D46A00"},
            {"label": "TROPICAL\nFLAT", "bg": "#EB7E23", "isBuilding": False, "actionKey": "#EB7E23"},
            {"label": "WET\n(MANGROVE)", "bg": "#4CAF50", "isBuilding": False, "actionKey": "#4CAF50"},
            {"label": "VEGETATED\n(RAINFOREST)", "bg": "#2F6F2F", "isBuilding": False, "actionKey": "#2F6F2F"},
        ],
        # Row 2
        [
            {"label": "TUNDRA\nROUGH", "bg": "#666666", "isBuilding": False, "actionKey": "#666666"},
            {"label": "TUNDRA\nFLAT",  "bg": "#999999", "isBuilding": False, "actionKey": "#999999"},
            {"label": "WET\n(BOG)",    "bg": "#444444", "isBuilding": False, "actionKey": "#444444"},
            {"label": "VEGETATED\n(TAIGA)", "bg": "#556B2F", "isBuilding": False, "actionKey": "#556B2F"},
            {"label": "GRASSLAND\nROUGH", "bg": "#38761D", "isBuilding": False, "actionKey": "#38761D"},
            {"label": "GRASSLAND\nFLAT",  "bg": "#4AA52E", "isBuilding": False, "actionKey": "#4AA52E"},
            {"label": "WET\n(MARSH)",  "bg": "#507F60", "isBuilding": False, "actionKey": "#507F60"},
            {"label": "VEGETATED\n(FOREST)", "bg": "#2E5808", "isBuilding": False, "actionKey": "#2E5808"},
        ],
        # Row 3
        [
            {"label": "PLAINS\nROUGH", "bg": "#D47F60", "isBuilding": False, "actionKey": "#D47F60"},
            {"label": "PLAINS\nFLAT",  "bg": "#F2AC83", "isBuilding": False, "actionKey": "#F2AC83"},
            {"label": "WET\n(WATERING)", "bg": "#EEB36D", "isBuilding": False, "actionKey": "#EEB36D"},
            {"label": "VEGETATED\n(SAVANNA)", "bg": "#F0AE50", "isBuilding": False, "actionKey": "#F0AE50"},
            {"label": "OPEN\nOCEAN",   "bg": "#1E90FF", "isBuilding": False, "actionKey": "#1E90FF"},
            {"label": "COASTAL",       "bg": "#66B3FF", "isBuilding": False, "actionKey": "#66B3FF"},
            {"label": "COASTAL\nLAKE", "bg": "#99CEFF", "isBuilding": False, "actionKey": "#99CEFF"},
            {"label": "NAVIGABLE\nRIVER", "bg": "#4682B4", "isBuilding": False, "actionKey": "#4682B4"},
        ],
        # Row 4
        [
            {"label": "NATURAL\nWONDER", "bg": "#CCCC00", "isBuilding": False, "actionKey": "#CCCC00"},
            {"label": "MOUNTAIN",        "bg": "#003366", "isBuilding": False, "actionKey": "#003366"},
            {"label": "VOLCANO",         "bg": "#FF4500", "isBuilding": False, "actionKey": "#FF4500"},
            {"label": "MINOR\nRIVER",    "bg": "#00AAAA", "isBuilding": False, "actionKey": "#00AAAA"},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
        ],
        # Row 5
        [
            {"label": "GRANARY",       "bg": "#006400", "isBuilding": True, "actionKey": "granary"},
            {"label": "FISHING\nQUAY", "bg": "#006400", "isBuilding": True, "actionKey": "fishing_quay"},
            {"label": "SAW PIT",       "bg": "#8B4513", "isBuilding": True, "actionKey": "saw_pit"},
            {"label": "BRICKYARD",     "bg": "#8B4513", "isBuilding": True, "actionKey": "brickyard"},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
        ],
        # Row 6
        [
            {"label": "GARDEN",       "bg": "#006400", "isBuilding": True, "actionKey": "garden"},
            {"label": "BATH",         "bg": "#006400", "isBuilding": True, "actionKey": "bath"},
            {"label": "MARKET",       "bg": "#B8860B", "isBuilding": True, "actionKey": "market"},
            {"label": "LIGHTHOUSE",   "bg": "#AA7E00", "isBuilding": True, "actionKey": "lighthouse"},
            {"label": "ANCIENT\nBRIDGE", "bg": "#BA9000", "isBuilding": True, "actionKey": "ancient_bridge"},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
        ],
        # Row 7
        [
            {"label": "LIBRARY",    "bg": "#333366", "isBuilding": True, "actionKey": "library"},
            {"label": "ACADEMY",    "bg": "#333366", "isBuilding": True, "actionKey": "academy"},
            {"label": "BARRACKS",   "bg": "#8B4513", "isBuilding": True, "actionKey": "barracks"},
            {"label": "BLACKSMITH", "bg": "#8B4513", "isBuilding": True, "actionKey": "blacksmith"},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
        ],
        # Row 8
        [
            {"label": "MONUMENT",       "bg": "#CC0000", "isBuilding": True, "actionKey": "monument"},
            {"label": "AMPHI\nTHEATRE", "bg": "#663399", "isBuilding": True, "actionKey": "amphitheater"},
            {"label": "ALTAR",          "bg": "#8B4513", "isBuilding": True, "actionKey": "altar"},
            {"label": "VILLA",          "bg": "#8B4513", "isBuilding": True, "actionKey": "villa"},
            {"label": "ARENA",          "bg": "#8B4513", "isBuilding": True, "actionKey": "arena"},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
            {"label": "", "bg": "#000000", "isBuilding": False, "actionKey": ""},
        ],
    ]

def build_excel_layout_html():
    """
    Builds the 8x8 HTML table (or grid) from the row data above.
    """
    rows = get_excel_grid_data()
    html = ['<div class="excel-grid">']
    for row in rows:
        # added a left margin so the entire row shifts right
        html.append('<div class="excel-row" style="margin-left:20px;">')
        for cell in row:
            label = cell["label"].replace("\n", "<br>")
            color = cell["bg"]
            is_bldg = cell["isBuilding"]
            key = cell["actionKey"]

            # Onclick logic
            if is_bldg:
                onclick = f"selectBuilding('{key}')"
            else:
                # if the color is empty or black, do nothing
                if not key or key == "#000000":
                    onclick = ""
                else:
                    onclick = f"setColor('{key}', this)"

            html.append(f'''
            <div class="excel-cell" style="background-color:{color};" onclick="{onclick}">
              {label}
            </div>
            ''')
        html.append('</div>')  # end row
    html.append('</div>')
    return "\n".join(html)

def get_menu_html():
    """
    Replaces the old approach with your EXACT 8×8 layout from Excel,
    placed in a scrollable panel on the right.
    """
    grid_content = build_excel_layout_html()
    return f'''
    <div class="excel-layout-container">
      {grid_content}
    </div>
    '''

#
# --- MAIN FLASK ROUTE ---
#

def index():
    tiles = generate_all_tiles(max_ring=3, size=1.0)
    svg_code = build_svg(tiles, svg_size=600)
    menu_html = get_menu_html()

    return f"""
    <html>
    <head>
      <title>Custom 8x8 Excel Layout</title>
      <style>
        body {{
          margin: 0;
          background-color: #000;
          color: #AAA;
          font-family: "Courier New", monospace;
          text-transform: uppercase;
          font-size: 12px;
          overflow-x: hidden;
        }}
        .page-title {{
          position: fixed;
          top: 2px;
          left: 2px;
          font-size: 9px;
          color: #777;
          z-index: 9999;
        }}
        .container {{
          display: flex;
          box-sizing: border-box;
          padding-bottom: 60px; /* room for pinned bar */
          height: 100vh;
        }}
        .left-panel {{
          flex: 0 0 66%;
          padding: 10px;
          background-color: #111;
          box-sizing: border-box;
        }}
        .right-panel {{
          flex: 0 0 34%;
          padding: 10px;
          background-color: #222;
          box-sizing: border-box;
          overflow-y: auto;
        }}
        #hex-svg .hex:hover {{
          stroke: #fff !important;
        }}

        /* 8x8 grid styling */
        .excel-layout-container {{
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }}
        .excel-grid {{
          display: flex;
          flex-direction: column;
          gap: 2px;
        }}
        .excel-row {{
          display: grid;
          grid-template-columns: repeat(8, 1fr);
          gap: 2px;
        }}
        .excel-cell {{
          width: 100%;
          height: 60px;
          text-align: center;
          line-height: 1.2em;
          font-size: 0.7em;
          border: 1px solid #333;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
        }}
        .excel-cell:hover {{
          outline: 1px solid #fff;
          outline-offset: -1px;
        }}

        /* PINNED ACTION BAR */
        .action-bar {{
          position: fixed;
          bottom: 0;
          left: 0;
          width: 100%;
          height: 50px;
          background-color: #111;
          box-shadow: 0 -2px 4px rgba(0,0,0,0.5);
          display: flex;
          justify-content: space-evenly;
          align-items: center;
          z-index: 10000;
        }}
        .action-button {{
          width: 110px;
          height: 36px;
          border: 1px solid #777;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.7em;
          font-weight: bold;
          background-color: #444;
          color: #DDD;
          text-transform: uppercase;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
          transition: background-color 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
        }}
        .action-button:hover {{
          border: 1px solid #fff;
          background-color: #555;
          box-shadow: 0 4px 6px rgba(0,0,0,0.4);
        }}
        #status-message {{
          position: fixed;
          bottom: 60px;
          right: 20px;
          padding: 5px 10px;
          border-radius: 4px;
          opacity: 0;
          transition: opacity 1s ease-out;
          font-size: 0.9em;
          background-color: #222;
          color: #EEE;
          z-index: 10001;
        }}
        #optimization-results {{
          margin-top: 20px;
          padding: 10px;
          border: 1px solid #777;
          border-radius: 4px;
          background-color: #333;
          color: #EEE;
        }}
        .result-item {{
          margin-bottom: 15px;
          padding: 10px;
          background-color: #222;
          border-radius: 4px;
        }}
        .result-item h3 {{
          margin: 0 0 10px 0;
          font-size: 1.1em;
        }}
        .yields {{
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin: 5px 0;
        }}
        .yields span {{
          padding: 2px 6px;
          background-color: #555;
          border-radius: 3px;
          font-size: 0.9em;
          color: #EEE;
        }}
        #optimized-layout {{
          margin-top: 20px;
        }}
      </style>  
      <script>
        var currentLayout = {{}};
        var currentBuildings = {{}};

        var selectedColor = null;
        var selectedBuilding = null;
        var lastAction = [];
        var statusTimeout = null;

        function setColor(color, btn) {{
          if (!color) return; 
          selectedColor = color;
          selectedBuilding = null;
          showStatusMessage("Terrain Color Selected: " + color);
        }}

        function selectBuilding(building) {{
          selectedBuilding = building;
          selectedColor = null;
          showStatusMessage("Building Selected: " + building.toUpperCase());
        }}

        function hexClickHandler(evt) {{
          var hex = evt.target;
          var tileLabel = hex.getAttribute("data-label");
          if (selectedColor) {{
            lastAction.push({{
              type: "terrain",
              element: hex,
              oldFill: hex.getAttribute("fill"),
              tile: tileLabel
            }});
            hex.setAttribute("fill", selectedColor);
            currentLayout[tileLabel] = selectedColor;
            showStatusMessage(tileLabel + ": Terrain set to " + selectedColor);
          }} else if (selectedBuilding) {{
            if (!currentBuildings[tileLabel]) {{
              currentBuildings[tileLabel] = [];
            }}
            if (currentBuildings[tileLabel].length >= 2) {{
              showStatusMessage(tileLabel + " already has 2 buildings.");
              return;
            }}
            lastAction.push({{
              type: "building",
              tile: tileLabel,
              building: selectedBuilding
            }});
            currentBuildings[tileLabel].push(selectedBuilding);
            showStatusMessage(tileLabel + ": Added " + selectedBuilding.toUpperCase());
          }}
        }}

        function applyToAll() {{
          if (!selectedColor) return;
          var hexes = document.getElementsByClassName("hex");
          for (var i = 0; i < hexes.length; i++) {{
            var hex = hexes[i];
            lastAction.push({{
              type: "terrain",
              element: hex,
              oldFill: hex.getAttribute("fill"),
              tile: hex.getAttribute("data-label")
            }});
            hex.setAttribute("fill", selectedColor);
            currentLayout[hex.getAttribute("data-label")] = selectedColor;
          }}
          showStatusMessage("All tiles set to " + selectedColor);
        }}

        function goBack() {{
          if (lastAction.length > 0) {{
            var action = lastAction.pop();
            if (action.type === "terrain") {{
              action.element.setAttribute("fill", action.oldFill);
              delete currentLayout[action.tile];
            }} else if (action.type === "building") {{
              var tile = action.tile;
              var idx = currentBuildings[tile].indexOf(action.building);
              if (idx !== -1) {{
                currentBuildings[tile].splice(idx, 1);
              }}
            }}
          }}
        }}

        function clearHexes() {{
          var defaultColors = {{ "0": "#333333", "1": "#444444", "2": "#555555", "3": "#666666" }};
          var hexes = document.getElementsByClassName("hex");
          for (var i = 0; i < hexes.length; i++) {{
            var ring = hexes[i].getAttribute("data-ring");
            hexes[i].setAttribute("fill", defaultColors[ring]);
          }}
          currentLayout = {{}};
          currentBuildings = {{}};
        }}

        function saveLayout() {{
          fetch('/api/save_layout', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ hexes: currentLayout }})
          }})
          .then(response => response.json())
          .then(data => {{
            if (data.status === 'success') {{
              showStatusMessage("Layout saved!");
            }} else {{
              showStatusMessage("Error saving layout");
            }}
          }});
        }}

        function calcYield() {{
          fetch('/api/manual_yields', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ hexes: currentLayout, buildings: currentBuildings }})
          }})
          .then(response => response.json())
          .then(data => {{
            if (data.status === 'success') {{
              displayResults(data.results);
            }} else {{
              showStatusMessage("Error in yield calculation");
            }}
          }});
        }}

        function displayResults(results) {{
          const container = document.getElementById('optimization-results');
          container.innerHTML = '';
          container.style.display = 'block';
          results.forEach((result) => {{
            const div = document.createElement('div');
            div.className = 'result-item';
            div.innerHTML = `
              <h3>${{result.building.toUpperCase()}}</h3>
              <p>Tile: ${{result.tile}}</p>
              <p>Total Yields:</p>
              <pre>${{JSON.stringify(result.yields.total_yields, null, 2)}}</pre>
              <p>Breakdown:</p>
              <pre>${{JSON.stringify({{ base: result.yields.base_yields, adjacency: result.yields.adjacency_yields, quarter: result.yields.quarter_yields }}, null, 2)}}</pre>
            `;
            container.appendChild(div);
          }});
        }}

        function showStatusMessage(message) {{
          var statusElem = document.getElementById("status-message");
          statusElem.textContent = message;
          statusElem.style.opacity = 1;
          if (statusTimeout) {{
            clearTimeout(statusTimeout);
          }}
          statusTimeout = setTimeout(function() {{
            statusElem.style.opacity = 0;
          }}, 1500);
        }}

        function reportAction() {{
          alert("Report coming soon!");
        }}

        window.addEventListener("load", function() {{
          var hexes = document.getElementsByClassName("hex");
          for (var i = 0; i < hexes.length; i++) {{
            hexes[i].addEventListener("click", hexClickHandler);
          }}
        }});
      </script>
    </head>
    <body>
      <div class="page-title">WHAT THE HEX</div>
      <div class="container">
        <div class="left-panel">
          {svg_code}
          <div id="optimized-layout"></div>
        </div>
        <div class="right-panel">
          {menu_html}
          <div id="optimization-results"></div>
        </div>
      </div>

      <!-- PINNED ACTION BAR -->
      <div class="action-bar">
        <button class="action-button" onclick="applyToAll()">APPLY ALL</button>
        <button class="action-button" onclick="goBack()">UNDO</button>
        <button class="action-button" onclick="saveLayout()">SAVE</button>
        <button class="action-button" onclick="clearHexes()">CLEAR</button>
        <button class="action-button" onclick="calcYield()">CALC YIELD</button>
        <button class="action-button" onclick="reportAction()">REPORT</button>
      </div>

      <div id="status-message"></div>
    </body>
    </html>
    """
