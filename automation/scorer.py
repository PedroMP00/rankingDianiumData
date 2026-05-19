import json
from pathlib import Path
import config


def load_iaaf_tables():
    """Load IAAF scoring tables from JSON file."""
    try:
        with open(config.IAAF_TABLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Warning: IAAF tables not found at {config.IAAF_TABLES_FILE}")
        return {}


def is_indoor_track(item):
    """Detect if event is indoor track (60m) or indoor season (Jan-Mar, Dec)."""
    event_lower = item.get('prueba', '').lower()
    if '60m' in event_lower or '60 m' in event_lower:
        return True

    if item.get('fecha') and '/' in item['fecha']:
        try:
            month = int(item['fecha'].split('/')[1])
            return (month >= 1 and month <= 3) or month == 12
        except (ValueError, IndexError):
            return False
    return False


def get_score(mark_str, event, gender, iaaf_tables):
    """
    Calculate IAAF points for a mark.

    Args:
        mark_str: Mark as string (e.g., "13.45", "1.85")
        event: Event name (e.g., "100m", "Salto de Altura")
        gender: "Masculino" or "Femenino"
        iaaf_tables: IAAF scoring tables dict

    Returns:
        Points (int), or 0 if calculation fails
    """
    if not mark_str or not event or not gender:
        return 0

    try:
        mark_float = float(mark_str.replace(',', '.'))
    except (ValueError, AttributeError):
        return 0

    if not iaaf_tables or event not in iaaf_tables:
        return 0

    event_tables = iaaf_tables[event]
    gender_key = 'M' if gender == 'Masculino' else 'F'

    if gender_key not in event_tables:
        return 0

    table = event_tables[gender_key]
    if not table:
        return 0

    for mark_threshold, points in sorted(table, key=lambda x: x[0], reverse=True):
        if mark_float >= mark_threshold:
            return int(points)

    return 0


def add_points_to_json(input_file, output_file, iaaf_tables):
    """
    Load JSON, add IAAF points, save to new file.

    Args:
        input_file: Input JSON path
        output_file: Output JSON path with points
        iaaf_tables: IAAF scoring tables
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    points_added = 0
    for item in data:
        points = get_score(
            item.get('marca'),
            item.get('prueba'),
            item.get('sexo'),
            iaaf_tables
        )
        item['puntos'] = points
        if points > 0:
            points_added += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"📊 Scored {points_added}/{len(data)} marks with IAAF tables")
    print(f"📄 Output: {output_file}\n")


def score_rankings(input_file, output_file=None):
    """
    Main function to add IAAF points to rankings JSON.

    Args:
        input_file: JSON file with rankings
        output_file: Output JSON (default: append _con_puntos.json)

    Returns:
        Number of records with points added
    """
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_con_puntos.json"

    iaaf_tables = load_iaaf_tables()

    print(f"📖 Loading IAAF tables...")
    print(f"📥 Input: {input_file}")

    add_points_to_json(input_file, output_file, iaaf_tables)
    return True


if __name__ == "__main__":
    score_rankings(str(config.OUTPUT_FILE_2026), str(config.OUTPUT_FILE_2026_POINTS))
