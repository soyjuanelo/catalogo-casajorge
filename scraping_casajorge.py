import requests
from bs4 import BeautifulSoup
import csv
import json
import re
import time

# URL base de la tienda
BASE_URL = "https://www.tiendacasajorge.com.ar/productos"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extraer_variantes(script_text):
    """ Extrae las variantes del JSON embebido en la página """
    try:
        match = re.search(r'LS\.variants\s*=\s*(\[\{.*?\}\]);', script_text)
        if not match:
            return []
        
        json_text = match.group(1)
        variantes = json.loads(json_text)
        
        productos = []
        for variante in variantes:
            nombre_color = variante.get("option0", "Sin color")
            precio = variante.get("price_number", 0)
            sku = variante.get("sku", "Sin SKU")
            
            productos.append({
                "color": nombre_color,
                "precio": precio,
                "sku": sku
            })
        
        return productos
    except Exception as e:
        print(f"Error extrayendo variantes: {e}")
        return []

def obtener_productos():
    """ Obtiene la lista de productos y sus enlaces """
    productos = []
    pagina = 1

    while True:
        url_pagina = f"{BASE_URL}?page={pagina}"
        print(f"Extrayendo productos de: {url_pagina}")
        respuesta = requests.get(url_pagina, headers=HEADERS)
        if respuesta.status_code != 200:
            print(f"Error al acceder a {url_pagina} (Código: {respuesta.status_code})")
            break
        
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        items = soup.find_all('a', class_='product-item')

        if not items:
            print(f"No se encontraron más productos en la página {pagina}. Terminando scraping.")
            break

        for item in items:
            enlace = item['href'] if 'href' in item.attrs else None
            if enlace and not enlace.startswith("http"):
                enlace = "https://www.tiendacasajorge.com.ar" + enlace
            
            if enlace:
                nombre, variantes = obtener_detalles_producto(enlace)
                for variante in variantes:
                    productos.append({
                        "nombre": nombre,
                        "color": variante["color"],
                        "precio": variante["precio"],
                        "sku": variante["sku"],
                        "enlace": enlace
                    })
            
            time.sleep(1)  # Evitar bloqueos del servidor

        pagina += 1

    return productos

def obtener_detalles_producto(url):
    """ Extrae el nombre y las variantes de un producto """
    try:
        respuesta = requests.get(url, headers=HEADERS)
        if respuesta.status_code != 200:
            print(f"Error al acceder a {url} (Código: {respuesta.status_code})")
            return None, []
        
        soup = BeautifulSoup(respuesta.text, 'html.parser')

        # Extraer nombre del producto
        nombre_meta = soup.find('meta', {'name': 'twitter:title'})
        nombre = nombre_meta['content'].strip() if nombre_meta else "Sin nombre"

        # Buscar el JSON dentro de un <script>
        scripts = soup.find_all("script")
        for script in scripts:
            if "LS.variants" in script.text:
                variantes = extraer_variantes(script.text)
                return nombre, variantes

        return nombre, []
    except Exception as e:
        print(f"Error procesando {url}: {e}")
        return None, []

def guardar_en_csv(productos, archivo="productos.csv"):
    """ Guarda los datos en un archivo CSV """
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=["nombre", "color", "precio", "sku", "enlace"])
        escritor.writeheader()
        escritor.writerows(productos)

productos = obtener_productos()
guardar_en_csv(productos)
print(f"Scraping completado. Se guardaron {len(productos)} productos en productos.csv")
