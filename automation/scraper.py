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
        # Carpeta temporal exclusiva para las descargas de Selenium en cada iteración
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

        # Configuramos Chrome para que descargue siempre en nuestra carpeta temporal limpia
        prefs = {
            "download.default_directory": str(self.tmp_download_dir),
            "download.prompt_for_download": False,
            "directory_upgrade": True,
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, config.SELENIUM_WAIT_TIME)

    def limpiar_carpeta_temporal(self):
        """Borra la carpeta temporal y la recrea completamente vacía."""
        if self.tmp_download_dir.exists():
            shutil.rmtree(self.tmp_download_dir)
        os.makedirs(self.tmp_download_dir, exist_ok=True)

    def aplicar_filtros_base(self, cat_val, sexo_val):
        self.driver.get(config.RFEA_URL)
        time.sleep(3)
        Select(self.wait.until(EC.presence_of_element_located((By.ID, "edit-season")))).select_by_value(str(self.year))
        time.sleep(1)
        Select(self.driver.find_element(By.ID, "edit-category")).select_by_value(cat_val)
        time.sleep(1)
        Select(self.driver.find_element(By.ID, "edit-gender")).select_by_value(sexo_val)
        time.sleep(3)

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

                    try:
                        self.aplicar_filtros_base(cat_val, sexo_val)
                    except Exception as e:
                        print(f"   ⚠️ Error aplicando filtros base: {str(e)[:40]}")
                        continue

                    try:
                        select_elem = Select(self.driver.find_element(By.ID, "edit-event"))
                        pruebas = [(opt.get_attribute("value"), opt.text) for opt in select_elem.options
                                  if opt.get_attribute("value") and "::" in opt.get_attribute("value")]
                        print(f"   Found {len(pruebas)} events")
                    except Exception as e:
                        print(f"   ⚠️ No se pudieron extraer eventos: {str(e)[:40]}")
                        continue

                    for p_val, p_text in pruebas:
                        nombre_fiscale = p_text.replace("/", "-").replace(" ", "_").replace("(", "").replace(")", "").strip()
                        final_path = ruta_destino / f"{nombre_fiscale}.xlsx"

                        if final_path.exists():
                            print(f"   ⏭️  {p_text}")
                            continue

                        print(f"   Processing: {p_text}...", end=" ", flush=True)
                        
                        # PASO CLAVE: Vaciamos la carpeta temporal antes de darle al botón
                        self.limpiar_carpeta_temporal()

                        try:
                            select_eventos = Select(self.wait.until(EC.presence_of_element_located((By.ID, "edit-event"))))
                            select_eventos.select_by_value(p_val)
                            time.sleep(2.5) 

                            btn_excel = self.wait.until(EC.element_to_be_clickable((By.ID, "export-excel-btn")))
                            self.driver.execute_script("arguments[0].click();", btn_excel)

                            descargado = False
                            # Esperamos a que aparezca el archivo en la carpeta limpia
                            for _ in range(config.SELENIUM_DOWNLOAD_TIMEOUT):
                                time.sleep(1)
                                archivos = [f for f in glob.glob(str(self.tmp_download_dir / "*.xlsx")) 
                                            if not f.endswith('.crdownload')]
                                
                                if archivos: # ¡Ha aparecido el archivo!
                                    shutil.move(archivos[0], final_path)
                                    downloaded_files.append(str(final_path))
                                    print("✅")
                                    descargado = True
                                    break
                            
                            if not descargado:
                                print("❌ (Timeout)")
                                # Si da timeout real, refrescamos la web por seguridad
                                self.aplicar_filtros_base(cat_val, sexo_val)

                        except Exception as e:
                            print(f"⚠️ (Error: {str(e)[:20]})")
                            try: self.aplicar_filtros_base(cat_val, sexo_val)
                            except: pass

            print("\n🏁 DOWNLOAD COMPLETE")
            return downloaded_files

        finally:
            if self.driver:
                self.driver.quit()
            # Limpieza final al terminar el script
            if self.tmp_download_dir.exists():
                shutil.rmtree(self.tmp_download_dir)


def download_year(year, headless=True):
    scraper = RFEAScraper(year, headless=headless)
    return scraper.download_all()