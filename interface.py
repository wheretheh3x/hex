import math
from flask import Flask

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
    return (xA + frac * (xB - xA), yA + frac * (yB - yA))

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
    return [(cx + size * math.cos(math.radians(60 * k)),
             cy + size * math.sin(math.radians(60 * k)))
            for k in range(6)]

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
                tiles.append({'label': f"({r},{i})", 'ring': r, 'index': i, 'corners': corners})
    return tiles

def build_svg(tiles, svg_size=600):
    min_x = min(x for t in tiles for (x, _) in t['corners'])
    max_x = max(x for t in tiles for (x, _) in t['corners'])
    min_y = min(y for t in tiles for (_, y) in t['corners'])
    max_y = max(y for t in tiles for (_, y) in t['corners'])
    scale = (svg_size - 10) / max(max_x - min_x, max_y - min_y)
    color_map = {0: '#F4F4F4', 1: '#EDEDED', 2: '#E6E6E6', 3: '#DFDFDF'}

    svg = [f'<svg id="hex-svg" width="{svg_size}" height="{svg_size}" viewBox="0 0 {svg_size} {svg_size}" xmlns="http://www.w3.org/2000/svg">']

    for t in tiles:
        pts = []
        for (x, y) in t['corners']:
            sx = (x - min_x) * scale + 5
            sy = (max_y - y) * scale + 5
            pts.append(f"{sx},{sy}")
        pts_str = " ".join(pts)

        col = color_map.get(t['ring'], '#CCCCCC')
        svg.append(
            f'<polygon class="hex" data-ring="{t["ring"]}" data-label="{t["label"]}" '
            f'fill="{col}" points="{pts_str}" '
            f'style="stroke:#999;stroke-width:1;cursor:pointer; transition: fill 0.3s ease;" />'
        )

        # Now add a text label in the middle of the polygon
        avg_x = sum(x for (x, _) in t['corners']) / 6
        avg_y = sum(y for (_, y) in t['corners']) / 6
        sx_center = (avg_x - min_x) * scale + 5
        sy_center = (max_y - avg_y) * scale + 5

        # We use a small font-size=10 and anchor middle
        svg.append(
            f'<text x="{sx_center}" y="{sy_center}" font-size="10" fill="black" text-anchor="middle">'
            f'{t["label"]}</text>'
        )

    svg.append('</svg>')
    return "\n".join(svg)

def get_menu_html():
    """Return the menu HTML"""
    return """
    <div class="menu">
      <div class="menu-section">
        <div class="menu-category">ADJACENCY BONUSES</div>
        <div class="menu-buttons" style="margin-bottom:10px;">
          <button class="menu-button" style="background-color: #003366; color: white;" onclick="setColor('#003366', this)">MOUNTAIN</button>
          <button class="menu-button" style="background-color: #444444; color: white;" onclick="setColor('#444444', this)">NATURAL WONDER</button>
          <button class="menu-button" style="background-color: #5D4037; color: white;" onclick="setColor('#5D4037', this)">RESOURCES</button>
        </div>
        <div class="menu-buttons">
          <button class="menu-button" style="background-color: #1E90FF; color: white;" onclick="setColor('#1E90FF', this)">OPEN OCEAN</button>
          <button class="menu-button" style="background-color: #66B3FF; color: black;" onclick="setColor('#66B3FF', this)">COAST</button>
          <button class="menu-button" style="background-color: #00CED1; color: white;" onclick="setColor('#00CED1', this)">COASTAL LAKE</button>
          <button class="menu-button" style="background-color: #4682B4; color: white;" onclick="setColor('#4682B4', this)">NAVIGABLE RIVER</button>
        </div>
      </div>
      <div class="menu-section">
        <div class="menu-category">DESERT</div>
        <div class="menu-buttons">
          <button class="menu-button" style="background-color: #C5984C; color: white;" onclick="setColor('#C5984C', this)">FLAT</button>
          <button class="menu-button" style="background-color: #A67C39; color: white;" onclick="setColor('#A67C39', this)">ROUGH</button>
        </div>
      </div>
      <div class="menu-section">
        <div class="menu-category">TROPICAL</div>
        <div class="menu-buttons">
          <button class="menu-button" style="background-color: #FFB347; color: black;" onclick="setColor('#FFB347', this)">FLAT</button>
          <button class="menu-button" style="background-color: #FF8C69; color: white;" onclick="setColor('#FF8C69', this)">ROUGH</button>
        </div>
      </div>
      <div class="menu-section">
        <div class="menu-category">GRASSLAND</div>
        <div class="menu-buttons">
          <button class="menu-button" style="background-color: #566F18; color: white;" onclick="setColor('#566F18', this)">FLAT</button>
          <button class="menu-button" style="background-color: #4B5C16; color: white;" onclick="setColor('#4B5C16', this)">ROUGH</button>
        </div>
      </div>
      <div class="menu-section">
        <div class="menu-category">PLAINS</div>
        <div class="menu-buttons">
          <button class="menu-button" style="background-color: #9E9136; color: white;" onclick="setColor('#9E9136', this)">FLAT</button>
          <button class="menu-button" style="background-color: #8C7F30; color: white;" onclick="setColor('#8C7F30', this)">ROUGH</button>
        </div>
      </div>
      <div class="menu-section">
        <div class="menu-category">TUNDRA</div>
        <div class="menu-buttons">
          <button class="menu-button" style="background-color: #B8B8A4; color: black;" onclick="setColor('#B8B8A4', this)">FLAT</button>
          <button class="menu-button" style="background-color: #A0A09A; color: white;" onclick="setColor('#A0A09A', this)">ROUGH</button>
        </div>
      </div>
      <div class="menu-actions">
        <button class="action-button" onclick="applyToAll()">APPLY TO ALL</button>
        <button class="action-button" onclick="goBack()">GO BACK</button>
        <button class="action-button" onclick="saveLayout()">SAVE</button>
        <button class="action-button" onclick="clearHexes()">CLEAR</button>
        <button class="action-button" onclick="optimizeLayout()">OPTIMIZE</button>
      </div>
      <div id="optimization-results" style="display:none;"></div>
    </div>
    """

def index():
    """Render the main interface with two diagrams:
       1) The base diagram for editing (with labeled hexes)
       2) A second diagram (added after optimization) for final arrangement
    """
    tiles = generate_all_tiles(max_ring=3, size=1.0)
    svg_code = build_svg(tiles, svg_size=600)
    menu_html = get_menu_html()

    return f"""
    <html>
    <head>
      <title>Settlement Spot Inputs</title>
      <style>
        body {{
          margin: 0;
          font-family: Helvetica, sans-serif;
          text-transform: uppercase;
          font-size: 12px;
          overflow-y: auto;
        }}
        .page-title {{
          position: fixed;
          top: 2px;
          left: 2px;
          font-size: 9px;
          color: grey;
          z-index: 1000;
        }}
        .container {{
          display: flex;
          height: 70vh;
          align-items: flex-start;
          padding-top: 20px;
        }}
        .left-panel {{
          flex: 0 0 66.66%;
          padding: 10px;
          background-color: #F9F9F9;
          box-sizing: border-box;
        }}
        .right-panel {{
          flex: 0 0 33.34%;
          padding: 10px;
          background-color: #FFFFFF;
          box-sizing: border-box;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }}
        .bottom-container {{
          width: 100%;
          padding: 20px 10px;
          box-sizing: border-box;
          text-align: center;
          margin-top: 20px;
        }}
        .menu {{
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 20px;
        }}
        .menu-section {{
          border: 1px solid #AAA;
          border-radius: 4px;
          padding: 4px;
        }}
        .menu-category {{
          font-weight: bold;
          margin-bottom: 4px;
          font-size: 0.85em;
          text-align: center;
        }}
        .menu-buttons {{
          display: flex;
          gap: 5px;
          justify-content: space-between;
        }}
        .menu-button {{
          flex: 1;
          height: 28px;
          padding: 2px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.7em;
          white-space: nowrap;
          font-weight: bold;
        }}
        .menu-actions {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          border: 1px solid #AAA;
          border-radius: 4px;
          padding: 10px;
        }}
        .action-button {{
          width: 100%;
          height: 36px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.85em;
          background-color: #BBB;
          font-weight: bold;
        }}
        #status-message {{
          position: fixed;
          bottom: 20px;
          right: 20px;
          padding: 5px 10px;
          border-radius: 4px;
          opacity: 0;
          transition: opacity 1s ease-out;
          font-size: 0.9em;
        }}
        #optimization-results {{
          margin-top: 20px;
          padding: 10px;
          border: 1px solid #DDD;
          border-radius: 4px;
        }}
        .result-item {{
          margin-bottom: 15px;
          padding: 10px;
          background-color: #F5F5F5;
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
          background-color: #E0E0E0;
          border-radius: 3px;
          font-size: 0.9em;
        }}
        #optimized-layout {{
          margin-top: 20px;
        }}
      </style>
      <script>
        var selectedColor = null;
        var selectedDescription = "";
        var lastAction = [];
        var statusTimeout = null;
        var currentLayout = {{}};

        // We'll store a global copy of the base tiles from Python so we can build the second diagram
        var tilesData = {tiles};

        function setColor(color, btn) {{
          selectedColor = color;
          var buttons = document.getElementsByClassName("menu-button");
          for (var i = 0; i < buttons.length; i++) {{
            buttons[i].style.fontWeight = "bold";
            buttons[i].style.border = "none";
          }}
          btn.style.fontWeight = "normal";
          btn.style.border = "1px solid red";
          var categoryElem = btn.parentNode.previousElementSibling;
          var category = categoryElem ? categoryElem.textContent.trim() : "";
          selectedDescription = btn.textContent.trim() + " " + category;
          showStatusMessage("(" + selectedDescription + ")");
        }}

        function changeHexColor(evt) {{
          if (selectedColor) {{
            var hex = evt.target;
            var tileLabel = hex.getAttribute("data-label");
            lastAction.push({{
              element: hex,
              oldFill: hex.getAttribute("fill"),
              oldPosition: tileLabel
            }});
            hex.setAttribute("fill", selectedColor);
            currentLayout[tileLabel] = selectedColor;
            showStatusMessage(tileLabel + ": " + selectedDescription);
          }}
        }}

        function applyToAll() {{
          if (selectedColor) {{
            var hexes = document.getElementsByClassName("hex");
            for (var i = 0; i < hexes.length; i++) {{
              var hex = hexes[i];
              lastAction.push({{
                element: hex,
                oldFill: hex.getAttribute("fill"),
                oldPosition: hex.getAttribute("data-label")
              }});
              hex.setAttribute("fill", selectedColor);
              currentLayout[hex.getAttribute("data-label")] = selectedColor;
            }}
            showStatusMessage("(ALL): " + selectedDescription);
          }}
        }}

        function goBack() {{
          if (lastAction.length > 0) {{
            var action = lastAction.pop();
            action.element.setAttribute("fill", action.oldFill);
            delete currentLayout[action.oldPosition];
          }}
        }}

        function clearHexes() {{
          var defaultColors = {{"0": "#F4F4F4", "1": "#EDEDED", "2": "#E6E6E6", "3": "#DFDFDF"}};
          var hexes = document.getElementsByClassName("hex");
          for (var i = 0; i < hexes.length; i++) {{
            var ring = hexes[i].getAttribute("data-ring");
            hexes[i].setAttribute("fill", defaultColors[ring]);
          }}
          currentLayout = {{}};
        }}

        function saveLayout() {{
          fetch('/api/save_layout', {{
            method: 'POST',
            headers: {{
              'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
              hexes: currentLayout
            }})
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

        function optimizeLayout() {{
          fetch('/api/optimize', {{
            method: 'POST',
            headers: {{
              'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
              hexes: currentLayout,
              // Example building list
              buildings: ["monument"],
              priorities: {{
                "culture": 1.0
              }}
            }})
          }})
          .then(response => response.json())
          .then(data => {{
            if (data.status === 'success') {{
              displayResults(data.results);
            }} else {{
              showStatusMessage("Error in optimization");
            }}
          }});
        }}

        function displayResults(results) {{
          // 1) Clear out old results
          const container = document.getElementById('optimization-results');
          container.innerHTML = '';
          container.style.display = 'block';

          // 2) Build the table of results
          results.forEach((result, index) => {{
            const div = document.createElement('div');
            div.className = 'result-item';
            div.innerHTML = `
              <h3>${{result.building}}</h3>
              <p>Position: Ring ${{result.position[0]}}, Index ${{result.position[1]}}</p>
              <p>Score: ${{result.score.toFixed(2)}}</p>
              <div class="yields">
                ${{Object.entries(result.yields.total_yields)
                  .filter(([_, value]) => value > 0)
                  .map(([type, value]) => `<span>${{type}}: ${{value}}</span>`)
                  .join('')}}
              </div>
            `;
            container.appendChild(div);
          }});

          // 3) Build a second diagram showing final arrangement
          const svgHTML = generateOptimizedSVG(tilesData, results);
          const layoutDiv = document.getElementById('optimized-layout');
          layoutDiv.innerHTML = svgHTML;
        }}

        function generateOptimizedSVG(tiles, results) {{
          // Convert results into a dictionary keyed by (ring,index) => [buildingNames...]
          let assignmentMap = {{}};
          results.forEach(r => {{
            let ring = r.position[0];
            let idx = r.position[1];
            let key = `${{ring}},${{idx}}`;
            if (!assignmentMap[key]) {{
              assignmentMap[key] = [];
            }}
            assignmentMap[key].push(r.building);
          }});

          // We'll build an SVG similar to build_svg, but also add <text> with building names
          let svgSize = 600;
          // Find bounding box
          let allX = [];
          let allY = [];
          tiles.forEach(t => {{
            t.corners.forEach(pt => {{
              allX.push(pt[0]);
              allY.push(pt[1]);
            }});
          }});
          const min_x = Math.min(...allX);
          const max_x = Math.max(...allX);
          const min_y = Math.min(...allY);
          const max_y = Math.max(...allY);
          const scale = (svgSize - 10) / Math.max((max_x - min_x), (max_y - min_y));

          // We'll color the rings lightly, then place text if there's a building
          let colorMap = {{0: '#F4F4F4', 1: '#EDEDED', 2: '#E6E6E6', 3: '#DFDFDF'}};
          let svg = [];
          svg.push(`<svg width="${{svgSize}}" height="${{svgSize}}" viewBox="0 0 ${{svgSize}} ${{svgSize}}" xmlns="http://www.w3.org/2000/svg">`);

          tiles.forEach(tile => {{
            let pts = [];
            tile.corners.forEach(([x, y]) => {{
              let sx = (x - min_x) * scale + 5;
              let sy = (max_y - y) * scale + 5;
              pts.push(`${{sx}},${{sy}}`);
            }});
            let pts_str = pts.join(" ");
            let col = colorMap[tile.ring] || '#CCCCCC';
            svg.push(`<polygon fill="${{col}}" stroke="#999" stroke-width="1" points="${{pts_str}}"></polygon>`);

            // If there are buildings assigned to this tile, place them in the center as text
            let key = `${{tile.ring}},${{tile.index}}`;
            if (assignmentMap[key]) {{
              // Find tile center
              let avgX = 0; 
              let avgY = 0;
              tile.corners.forEach(([cx, cy]) => {{
                avgX += cx;
                avgY += cy;
              }});
              avgX = avgX / tile.corners.length;
              avgY = avgY / tile.corners.length;
              // Scale them
              let textX = (avgX - min_x) * scale + 5;
              let textY = (max_y - avgY) * scale + 5;

              // Join building names
              let bldgNames = assignmentMap[key].join(", ");

              svg.push(`
                <text x="${{textX}}" y="${{textY}}" font-size="10" fill="black" text-anchor="middle">
                  ${{bldgNames}}
                </text>
              `);
            }}
          }});

          svg.push('</svg>');
          return svg.join('');
        }}

        function showStatusMessage(message) {{
          var statusElem = document.getElementById("status-message");
          statusElem.textContent = message;
          statusElem.style.color = selectedColor;
          statusElem.style.opacity = 1;
          if (statusTimeout) {{
            clearTimeout(statusTimeout);
          }}
          statusTimeout = setTimeout(function() {{
            statusElem.style.opacity = 0;
          }}, 1000);
        }}

        window.addEventListener("load", function() {{
          var hexes = document.getElementsByClassName("hex");
          for (var i = 0; i < hexes.length; i++) {{
            hexes[i].addEventListener("click", changeHexColor);
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
        </div>
      </div>
      <div id="status-message"></div>
      <div class="bottom-container" id="saved-image-container"></div>
    </body>
    </html>
    """

