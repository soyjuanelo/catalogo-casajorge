import requests
from bs4 import BeautifulSoup
import csv
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuración del navegador con Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Ejecutar en modo headless (sin ventana)
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# URL base de la sección de productos
BASE_URL = "https://www.tiendacasajorge.com.ar/productos"

def obtener_links_productos():
    """
    Recorre las páginas de la lista de productos y extrae los enlaces usando el selector "a.item-link".
    """
    links = []
    pagina = 1
    while True:
        url = f"{BASE_URL}?page={pagina}"
        print(f"Extrayendo links de: {url}")
        driver.get(url)
        time.sleep(5)  # Espera a que se cargue la página
        # Usamos el selector "a.item-link" basado en el HTML mostrado
        elementos = driver.find_elements(By.CSS_SELECTOR, "a.item-link")
        if not elementos:
            print(f"No se encontraron enlaces en la página {pagina}. Terminando.")
            break
        for elem in elementos:
            href = elem.get_attribute("href")
            if href:
                links.append(href)
        pagina += 1
    return links

def extraer_detalles_producto(url):
    """
    Ingresa a la página de detalle de un producto y extrae:
      - El nombre del producto (usando el meta tag twitter:title).
      - El JSON de variantes (LS.variants) y de allí extrae SKU, color (option0) y precio (price_number).
    Retorna una lista de registros (uno por variante) con los campos deseados.
    """
    print(f"Procesando producto: {url}")
    driver.get(url)
    time.sleep(5)
    
    # Extraer nombre del producto
    nombre = "Sin nombre"
    try:
        meta_nombre = driver.find_element(By.CSS_SELECTOR, "meta[name='twitter:title']")
        nombre = meta_nombre.get_attribute("content").strip()
    except Exception as e:
        print(f"Error extrayendo nombre en {url}: {e}")
    
    # Buscar en los <script> el fragmento con "LS.variants"
    variantes = []
    try:
        scripts = driver.find_elements(By.TAG_NAME, "script")
        for script in scripts:
            script_text = script.get_attribute("innerHTML")
            if "LS.variants" in script_text:
                match = re.search(r'LS\.variants\s*=\s*(\[\{.*?\}\]);', script_text, re.DOTALL)
                if match:
                    json_text = match.group(1)
                    variantes = json.loads(json_text)
                    break
    except Exception as e:
        print(f"Error extrayendo variantes en {url}: {e}")
    
    registros = []
    for var in variantes:
        sku = var.get("sku", "Sin SKU")
        color = var.get("option0", "Sin color")
        precio = var.get("price_number", 0)
        registros.append({
            "nombre": nombre,
            "sku": sku,
            "color": color,
            "precio": precio,
            "enlace": url
        })
    return registros

def extraer_todos_los_productos():
