import pandas as pd
import json
import os
from pathlib import Path
import config


def clean_value(value):
    if pd.isna(value) or str(value).lower() == "nan":
        return ""
    return str(value).strip()


def get_category_weight(category):
    return config.CATEGORY_WEIGHTS.get(category, 99)


def import_and_export(input_dir, output_file, club_name=None, mode="2026"):
    """
    Read Excel files and export to JSON.

    Args:
        input_dir: Path to folder containing year/category/gender/*.xlsx structure
        output_file: Output JSON file path
        club_name: Filter by club name (default: CLUB_NAME from config)
        mode: '2026' for current season only, 'historical' for all years
    """
    if club_name is None:
        club_name = config.CLUB_NAME

    input_dir = Path(input_dir)
    output_file = Path(output_file)
    all_marks = []
    file_count = 0

    print(f"--- 🏃 Starting import from {input_dir} ---")
    print(f"    Mode: {mode}, Club: {club_name}")

    for root, dirs, files in os.walk(input_dir):
        parts = root.replace("\\", "/").split("/")
        year = next((p for p in parts if p.isdigit() and len(p) == 4), "Unknown")

        if mode == "2026" and year != "2026":
            continue
        if mode == "historical" and year == "2026":
            continue

        for file in files:
            if file.endswith(".xlsx") and not file.startswith("~$"):
                file_count += 1
                full_path = os.path.join(root, file)

                category = parts[-2] if len(parts) >= 2 else "Other"
                gender = parts[-1] if len(parts) >= 1 else "Unknown"

                try:
                    df_title = pd.read_excel(full_path, header=None, nrows=1)
                    event_name = str(df_title.iloc[0, 0]).split("Sub")[0].strip()

                    df_raw = pd.read_excel(full_path, header=None)
                    header_row = 0
                    for i, row in df_raw.iterrows():
                        if "CLUB" in [str(v).upper() for v in row.values]:
                            header_row = i
                            break

                    df = pd.read_excel(full_path, skiprows=header_row)
                    df.columns = [str(c).strip().upper() for c in df.columns]

                    last_rank = 0
                    for idx, row in df.iterrows():
                        rank_val = str(row.get("RANK", "")).strip()
                        if rank_val.isdigit():
                            last_rank = int(rank_val)
                        else:
                            last_rank += 1

                        if club_name.upper() in str(row.get("CLUB", "")).upper():
                            all_marks.append({
                                "nombre": clean_value(row.get("ATLETA")),
                                "marca": clean_value(row.get("MARCA")),
                                "viento": clean_value(row.get("VIENTO")),
                                "fecha": clean_value(row.get("FECHA")),
                                "lugar": clean_value(row.get("CIUDAD")),
                                "categoria": category,
                                "sexo": gender,
                                "prueba": event_name,
                                "rank": str(last_rank),
                                "temporada": year,
                                "puntos": 0
                            })

                except Exception as e:
                    print(f"    ❌ {file}: {str(e)[:50]}")

    # Deduplication: keep lowest category weight
    marks_final = {}
    for mark in all_marks:
        key = f"{mark['nombre']}_{mark['prueba']}_{mark['marca']}_{mark['fecha']}_{mark['temporada']}"

        if key not in marks_final:
            marks_final[key] = mark
        else:
            new_cat_weight = get_category_weight(mark['categoria'])
            old_cat_weight = get_category_weight(marks_final[key]['categoria'])
            if new_cat_weight < old_cat_weight:
                marks_final[key] = mark

    os.makedirs(output_file.parent, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(list(marks_final.values()), f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"📂 Files processed: {file_count}")
    print(f"🏆 Unique marks saved: {len(marks_final)}")
    print(f"📄 Output: {output_file}")
    print(f"{'='*50}\n")

    return len(marks_final)


def compile_all_years(data2026_file, historical_file, output_file):
    """
    Compile 2026 data + historical data into a single JSON file.
    Historical data is static, 2026 is updated weekly.

    Args:
        data2026_file: Path to data2026.json (with IAAF points)
        historical_file: Path to dataOld.json (static historical data)
        output_file: Path to output compiled JSON
    """
    all_data = []

    # Load historical data (2024-2025)
    if Path(historical_file).exists():
        try:
            with open(historical_file, "r", encoding="utf-8") as f:
                historical = json.load(f)
                all_data.extend(historical)
                print(f"✅ Loaded {len(historical)} historical records")
        except Exception as e:
            print(f"⚠️  Could not load historical data: {str(e)}")

    # Load 2026 data
    if Path(data2026_file).exists():
        try:
            with open(data2026_file, "r", encoding="utf-8") as f:
                data2026 = json.load(f)
                all_data.extend(data2026)
                print(f"✅ Loaded {len(data2026)} current year records")
        except Exception as e:
            print(f"⚠️  Could not load 2026 data: {str(e)}")

    # Sort by year (temporada) desc, then by athlete name
    all_data.sort(key=lambda x: (-int(x.get("temporada", 0)), x.get("nombre", "")))

    # Save compiled file
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"📦 Compiled JSON created: {output_file}")
    print(f"📊 Total records: {len(all_data)}")
    print(f"{'='*50}\n")

    return len(all_data)


if __name__ == "__main__":
    import_and_export(
        str(config.EXCEL_PROCESSING_DIR / "2026"),
        str(config.OUTPUT_FILE_2026),
        mode="2026"
    )
