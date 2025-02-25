from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from pathlib import Path
from backend.city_layout import CityLayout
from backend.layout_storage import LayoutStorage
from backend.optimizer import CityOptimizer
from interface import generate_all_tiles, build_svg, main_route as render_interface

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(
    filename='hex_optimizer.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

storage = LayoutStorage()

@app.route('/')
def index():
    return render_interface()

@app.route('/api/save_layout', methods=['POST'])
def save_layout():
    """Save current layout"""
    try:
        data = request.json
        hex_data = data.get('hexes', {})
        name = data.get('name')

        filename = storage.save_layout(hex_data, name)
        logging.info(f"Saved layout {filename}")

        return jsonify({"status": "success", "filename": filename})
    except Exception as e:
        logging.error(f"Error saving layout: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/optimize', methods=['POST'])
def optimize():
    """Run optimization for current layout"""
    try:
        data = request.json
        hex_data = data.get('hexes', {})
        buildings = data.get('buildings', [])
        priorities = data.get('priorities', {})

        # Create CityLayout from hex data
        city = storage.create_city_layout(hex_data)

        # Instantiate the backtracking optimizer
        optimizer = CityOptimizer(city)

        # Run global optimization
        results = optimizer.optimize_multiple_buildings(buildings, priorities)

        # Log the optimization request
        logging.info(f"Optimization request - Buildings: {buildings}, "
                     f"Priorities: {priorities}")

        # Convert results for JSON response
        output = []
        for r in results:
            output.append({
                "building": r.building,
                "position": r.position,
                "yields": r.yields,
                "score": r.score
            })

        return jsonify({
            "status": "success",
            "results": output
        })
    except Exception as e:
        logging.exception("Error in optimization")  # logs the entire traceback
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
