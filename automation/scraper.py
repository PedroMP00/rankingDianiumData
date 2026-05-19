import os
import time
import glob
import shutil
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import config

class RFEAScraper:
    def __init__(self, year, headless=True):
        self.year = year
        self.base_dir = config.EXCEL_DOWNLOAD_DIR / str(year)
        self.headless = headless
        self.driver = None
        self.wait = None

    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # CORRECCIÓN: Opción necesaria para que Chrome headless no crashee en GitHub Actions
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200,800")

        prefs = {
            "download.default_directory": str(self.base_dir),
            "download.prompt_for_download": False,
            "directory_upgrade": True,
        }
        options.add_experimental_option("prefs", prefs)

        # CORRECCIÓN: Quitamos webdriver-manager. Selenium detecta el driver de forma nativa.
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, config.SELENIUM_WAIT_TIME)

    def get_latest_file(self):
        archivos = [f for f in glob.glob(str(self.base_dir / "**" / "*.xlsx"), recursive=True)
                    if not f.endswith('.crdownload')]
        if not archivos:
            return None
        return max(archivos, key=os.path.getmtime)

    def download_all(self):
        os.makedirs(self.base_dir, exist_ok=True)
        self.setup_driver()

        try:
            downloaded_files = []

            for cat_nombre, cat_val in config.CATEGORIES.items():
                for sexo_nombre, sexo_val in config.GENDERS.items():
                    ruta_destino = self.base_dir / cat_nombre / sexo_nombre
                    os.makedirs(ruta_destino, exist_ok=True)

                    print(f"\n🚀 {cat_nombre} - {sexo_nombre}")

                    self.driver.get(config.RFEA_URL)
                    time.sleep(2)

                    try:
                        Select(self.wait.until(EC.presence_of_element_located((By.ID, "edit-season")))).select_by_value(str(self.year))
                        time.sleep(0.5)
                        Select(self.driver.find_element(By.ID, "edit-category")).select_by_value(cat_val)
                        time.sleep(0.5)
                        Select(self.driver.find_element(By.ID, "edit-gender")).select_by_value(sexo_val)
                        time.sleep(2)
                    except Exception as e:
                        print(f"   ⚠️ Error setting filters: {e}")
                        continue

                    try:
                        select_elem = Select(self.driver.find_element(By.ID, "edit-event"))
                        pruebas = [(opt.get_attribute("value"), opt.text) for opt in select_elem.options
                                  if opt.get_attribute("value") and "::" in opt.get_attribute("value")]
                        print(f"   Found {len(pruebas)} events")
                    except Exception as e:
                        print(f"   ⚠️ No events found: {e}")
                        continue

                    for p_val, p_text in pruebas:
                        nombre_fiscale = p_text.replace("/", "-").replace(" ", "_").replace("(", "").replace(")", "").strip()
                        final_path = ruta_destino / f"{nombre_fiscale}.xlsx"

                        if final_path.exists():
                            print(f"   ⏭️  {p_text}")
                            continue

                        print(f"   Processing: {p_text}...", end=" ", flush=True)
                        archivo_antes = self.get_latest_file()

                        try:
                            Select(self.driver.find_element(By.ID, "edit-event")).select_by_value(p_val)
                            time.sleep(2.5)

                            btn_excel = self.driver.find_element(By.ID, "export-excel-btn")
                            self.driver.execute_script("arguments[0].click();", btn_excel)

                            descargado = False
                            for _ in range(config.SELENIUM_DOWNLOAD_TIMEOUT):
                                time.sleep(1)
                                archivo_actual = self.get_latest_file()
                                if archivo_actual and archivo_actual != archivo_antes:
                                    shutil.move(archivo_actual, final_path)
                                    downloaded_files.append(str(final_path))
                                    print("✅")
                                    descargado = True
                                    break
                            if not downgraded:
                                print("❌ (Timeout)")
                        except Exception as e:
                            print(f"⚠️ ({str(e)[:20]})")

            print("\n🏁 DOWNLOAD COMPLETE")
            return downloaded_files

        finally:
            self.driver.quit()


def download_year(year, headless=True):
    scraper = RFEAScraper(year, headless=headless)
    return scraper.download_all()