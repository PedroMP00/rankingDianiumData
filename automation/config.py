import os
from pathlib import Path

# CORRECCIÓN: Rutas blindadas para entornos de ejecución remotos (GitHub Actions)
AUTOMATION_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = AUTOMATION_DIR.parent
WEB_FTP_DIR = PROJECT_ROOT / "web_ftp"
DATA_DIR = WEB_FTP_DIR / "data"

CLUB_NAME = "Atletisme Dianium"
RFEA_URL = "https://atletismorfea.es/ranking"

CATEGORIES = {
    "Sub 14": "151",
    "Sub 16": "153",
    "Sub 18": "155",
    "Sub 20": "157",
    "Sub 23": "159",
    "Absoluto": "145"
}

GENDERS = {
    "Masculino": "1",
    "Femenino": "2"
}

CATEGORY_WEIGHTS = {
    "Sub 14": 1,
    "Sub 16": 2,
    "Sub 18": 3,
    "Sub 20": 4,
    "Sub 23": 5,
    "Absoluto": 6
}

EXCEL_DOWNLOAD_DIR = AUTOMATION_DIR / "excels_raw"
EXCEL_PROCESSING_DIR = AUTOMATION_DIR / "excels_raw"

OUTPUT_FILE_2026 = DATA_DIR / "data2026.json"
OUTPUT_FILE_2026_POINTS = DATA_DIR / "data2026_con_puntos.json"
OUTPUT_FILE_HISTORICAL = DATA_DIR / "dataOld.json"
OUTPUT_FILE_COMPILED = DATA_DIR / "dataCompleto.json"

IAAF_TABLES_FILE = AUTOMATION_DIR / "iaaf-2025.json"

SELENIUM_WAIT_TIME = 15
SELENIUM_DOWNLOAD_TIMEOUT = 15
SELENIUM_HEADLESS = True

os.makedirs(DATA_DIR, exist_ok=True)