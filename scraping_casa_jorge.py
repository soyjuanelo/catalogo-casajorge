import time
import csv
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        try:
            # Espera hasta que aparezca al menos un enlace de producto
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.item-link"))
            )
        except Exception as e:
            print(f"No se encontraron enlaces en la página {pagina}: {e}")
            break

        elementos = driver.find_elements(By.CSS_SELECTOR, "a.item-link")
        if not elementos:
            print(f"No se encontraron enlaces en la página {pagina}. Terminando.")
            break

        for elem in elementos:
            href = elem.get_attribute("href")
            if href and href not in links:
                links.append(href)
        print(f"Página {pagina}: {len(elementos)} enlaces encontrados.")
        pagina += 1
        time.sleep(2)  # Pausa para no saturar el servidor

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
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "meta[name='twitter:title']"))
        )
    except Exception as e:
        print(f"Error esperando meta tag en {url}: {e}")

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
    """
    Recorre todos los enlaces de productos obtenidos desde la página principal.
    """
    todos_productos = []
    links = obtener_links_productos()
    print(f"Total de enlaces obtenidos: {len(links)}")
    for link in links:
        datos = extraer_detalles_producto(link)
        if datos:
            todos_productos.extend(datos)
        time.sleep(1)  # Pausa para no saturar el servidor
    return todos_productos

def guardar_en_csv(productos, archivo="productos.csv"):
    """
    Guarda la lista de productos en un archivo CSV.
    """
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["sku", "nombre", "color", "precio", "enlace"]
        escritor = csv.DictWriter(f, fieldnames=fieldnames)
        escritor.writeheader()
        escritor.writerows(productos)

def main():
    productos = extraer_todos_los_productos()
    guardar_en_csv(productos)
    print(f"Scraping completado. Se guardaron {len(productos)} registros en productos.csv")
    driver.quit()

if __name__ == "__main__":
    main()
