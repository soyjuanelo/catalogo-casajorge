import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuración del navegador con Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Ejecutar en segundo plano
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Iniciar WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

BASE_URL = "https://www.tiendacasajorge.com.ar/productos"


def obtener_productos(url):
    productos = []
    driver.get(url)
    time.sleep(5)  # Esperar a que carguen los productos

    # Buscar contenedores de producto
    items = driver.find_elements(By.CSS_SELECTOR, ".js-item-product.item")
    for item in items:
        try:
            nombre = item.find_element(By.CSS_SELECTOR, "h6.js-product-name").text
        except Exception:
            nombre = "Sin nombre"
        try:
            precio = item.find_element(By.CSS_SELECTOR, "span.js-price-display").text
        except Exception:
            precio = "Sin precio"
        try:
            enlace = item.find_element(By.CSS_SELECTOR, "a.item-link").get_attribute("href")
        except Exception:
            enlace = "Sin enlace"
        try:
            imagen = item.find_element(By.TAG_NAME, "img").get_attribute("src")
        except Exception:
            imagen = "Sin imagen"

        productos.append({
            "nombre": nombre,
            "precio": precio,
            "enlace": enlace,
            "imagen": imagen
        })
    return productos


def extraer_todos_los_productos():
    pagina = 1
    todos_los_productos = []
    while True:
        url = f"{BASE_URL}?page={pagina}"
        print(f"Extrayendo: {url}")
        productos = obtener_productos(url)
        if not productos:
            break  # No se encontraron productos, terminamos
        todos_los_productos.extend(productos)
        pagina += 1
    return todos_los_productos


def guardar_en_csv(productos, archivo="productos.csv"):
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=["nombre", "precio", "enlace", "imagen"])
        escritor.writeheader()
        escritor.writerows(productos)


productos = extraer_todos_los_productos()
guardar_en_csv(productos)
print(f"Scraping completado. Se guardaron {len(productos)} productos en productos.csv")
driver.quit()
