# Hex

A city planning optimization tool for Civilization 7. Hex helps players optimize their city building placement by analyzing adjacency bonuses and constraints.

## Features (Planned)
- Optimize building placement based on adjacency rules
- Account for terrain constraints and special features
- Plan ahead for future building possibilities
- Visualize city layout and bonuses

## Development Setup
1. Create virtual environment:
```bash
py -m venv venv
```

2. Activate virtual environment:
```bash
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure
- `backend/`: Python backend code
  - `app.py`: Flask application
  - `optimizer.py`: Optimization logic
  - `rules/`: Game rules and constraints
- `frontend/`: Web interface (coming soon)
- `tests/`: Test suite