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
        self.tmp_download_dir = config.PROJECT_ROOT / "automation" / "tmp_downloads"
        self.headless = headless
        self.driver = None
        self.wait = None

    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200,800")

        prefs = {
            "download.default_directory": str(self.tmp_download_dir),
            "download.prompt_for_download": False,
            "directory_upgrade": True,
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, config.SELENIUM_WAIT_TIME)

    def limpiar_carpeta_temporal(self):
        if self.tmp_download_dir.exists():
            shutil.rmtree(self.tmp_download_dir)
        os.makedirs(self.tmp_download_dir, exist_ok=True)

    def inicializar_y_obtener_pruebas(self, cat_val, sexo_val):
        """Entra a la web, aplica los filtros base y extrae la lista de pruebas válidas."""
        self.driver.get(config.RFEA_URL)
        
        # Esperamos a que el desplegable de temporada esté listo y elegimos el año
        el_season = self.wait.until(EC.visibility_of_element_located((By.ID, "edit-season")))
        Select(el_season).select_by_value(str(self.year))
        time.sleep(1.5)

        # Seleccionamos categoría
        el_cat = self.wait.until(EC.visibility_of_element_located((By.ID, "edit-category")))
        Select(el_cat).select_by_value(cat_val)
        time.sleep(1.5)

        # Seleccionamos sexo
        el_gender = self.wait.until(EC.visibility_of_element_located((By.ID, "edit-gender")))
        Select(el_gender).select_by_value(sexo_val)
        time.sleep(3.5) # Tiempo clave para que la RFEA cargue el listado dinámico de eventos

        # Extraemos las opciones válidas
        el_event = self.wait.until(EC.presence_of_element_located((By.ID, "edit-event")))
        select_elem = Select(el_event)
        
        pruebas = []
        for opt in select_elem.options:
            val = opt.get_attribute("value")
            if val and "::" in val:
                pruebas.append((val, opt.text))
        return pruebas

    def download_all(self):
        os.makedirs(self.base_dir, exist_ok=True)
        self.limpiar_carpeta_temporal()
        self.setup_driver()

        try:
            downloaded_files = []

            for cat_nombre, cat_val in config.CATEGORIES.items():
                for sexo_nombre, sexo_val in config.GENDERS.items():
                    ruta_destino = self.base_dir / cat_nombre / sexo_nombre
                    os.makedirs(ruta_destino, exist_ok=True)

                    print(f"\n🚀 {cat_nombre} - {sexo_nombre}")

                    # Obtenemos la lista de pruebas de forma limpia
                    try:
                        pruebas = self.inicializar_y_obtener_pruebas(cat_val, sexo_val)
                        print(f"   Found {len(pruebas)} events")
                    except Exception as e:
                        print(f"   ⚠️ Error extrayendo listado de pruebas: {str(e)[:50]}")
                        continue

                    # Iteramos sobre cada prueba
                    for p_val, p_text in pruebas:
                        nombre_fiscale = p_text.replace("/", "-").replace(" ", "_").replace("(", "").replace(")", "").strip()
                        final_path = ruta_destino / f"{nombre_fiscale}.xlsx"

                        if final_path.exists():
                            print(f"   ⏭️  {p_text}")
                            continue

                        print(f"   Processing: {p_text}...", end=" ", flush=True)
                        self.limpiar_carpeta_temporal()

                        try:
                            # ESTRATEGIA MAESTRA: Recargamos la URL e introducemos los filtros de cero para cada prueba individual
                            # Esto evita CUALQUIER desincronización o elemento caducado (Stale Element)
                            self.driver.get(config.RFEA_URL)
                            
                            Select(self.wait.until(EC.visibility_of_element_located((By.ID, "edit-season")))).select_by_value(str(self.year))
                            time.sleep(1)
                            Select(self.wait.until(EC.visibility_of_element_located((By.ID, "edit-category")))).select_by_value(cat_val)
                            time.sleep(1)
                            Select(self.wait.until(EC.visibility_of_element_located((By.ID, "edit-gender")))).select_by_value(sexo_val)
                            time.sleep(2.5)

                            # Seleccionamos la prueba concreta
                            select_eventos = Select(self.wait.until(EC.visibility_of_element_located((By.ID, "edit-event"))))
                            select_eventos.select_by_value(p_val)
                            time.sleep(3.5) # Esperamos a que la RFEA busque y pinte el botón de Excel

                            # Hacemos clic en el botón de exportación
                            btn_excel = self.wait.until(EC.element_to_be_clickable((By.ID, "export-excel-btn")))
                            self.driver.execute_script("arguments[0].click();", btn_excel)

                            # Esperamos la descarga física del archivo
                            descargado = False
                            for _ in range(config.SELENIUM_DOWNLOAD_TIMEOUT):
                                time.sleep(1)
                                archivos = [f for f in glob.glob(str(self.tmp_download_dir / "*.xlsx")) 
                                            if not f.endswith('.crdownload')]
                                
                                if archivos:
                                    shutil.move(archivos[0], final_path)
                                    downloaded_files.append(str(final_path))
                                    print("✅")
                                    descargado = True
                                    break
                            
                            if not descargado:
                                print("❌ (Timeout)")

                        except Exception as e:
                            print(f"⚠️ (Error: {str(e)[:30]})")

            print("\n🏁 DOWNLOAD COMPLETE")
            return downloaded_files

        finally:
            if self.driver:
                self.driver.quit()
            if self.tmp_download_dir.exists():
                shutil.rmtree(self.tmp_download_dir)

def download_year(year, headless=True):
    scraper = RFEAScraper(year, headless=headless)
    return scraper.download_all()