# 🛒 amazon-scraper-fastapi

API REST construida con **FastAPI** y **BeautifulSoup4** que permite consultar y extraer información estructurada de productos de Amazon (búsquedas y detalle individual) mediante técnicas de web scraping.

> ⚠️ **Aviso de Propósito Educativo (Disclaimer)**  
> Este proyecto ha sido desarrollado **exclusivamente con fines pedagógicos y de aprendizaje** para practicar y consolidar conceptos de:
> - Lenguaje **Python** moderno (tipado estático, type narrowing, dataclasses/properties).
> - Creación de APIs REST asíncronas con **FastAPI**.
> - Modelado, validación y serialización de datos con **Pydantic v2**.
> - Manejo de solicitudes HTTP avanzadas con **Requests** (sesiones persistentes, headers personalizados).
> - Web Scraping y parseo del DOM con **BeautifulSoup4** (manejo de selectores dinámicos y defensivos).
> 
> *No está destinado para uso comercial ni producción masiva, respetando los Términos de Servicio de Amazon.*

---

## ✨ Características

- 🔍 **Búsqueda paginada (`/api/v1/items`)**: Búsqueda por palabras clave con soporte de navegación entre páginas (`page=1`, `page=2`, ...).
- 📦 **Detalle exhaustivo (`/api/v1/item`)**: Extracción de nombre, precio numérico, viñetas de especificaciones técnicas (`product_details`), imagen y enlace.
- 🧹 **Normalización de URLs Canónicas**: Limpieza automática de enlaces patrocinados (`/sspa/click`) y parámetros de tracking (`?ref=...`), reconstruyendo la URL limpia basada en el código ASIN: `https://www.amazon.es/dp/{ASIN}`.
- 🖼️ **Imágenes en Máxima Resolución**: Detección y supresión del filtro de compresión de Amazon para entregar la URL original en alta calidad.
- 🛡️ **Sanitización Unicode**: Purga de caracteres invisibles de dirección bidireccional (`\u200e`, `\u200f`) inyectados por Amazon.
- 🧱 **Arquitectura con Pydantic**: Validación estricta de tipos de datos y generación automática de esquemas OpenAPI.
- 🚦 **Gestión Semántica de Errores**: Captura de retos JavaScript anti-bot (`cloudflare-block`), elementos no localizados (`parse-error`) y búsquedas vacías (`no-results`).

---

## 🚀 Requisitos e Instalación

### Requisitos previos
- **Python 3.10+** (probado en Python 3.14)

### Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/amazon-scraper-fastapi.git
   cd amazon-scraper-fastapi
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # En Linux/macOS
   # .venv\Scripts\activate   # En Windows
   ```

3. Instala las dependencias:
   ```bash
   pip install fastapi uvicorn requests beautifulsoup4 pydantic
   ```

---

## 💻 Ejecución

Inicia el servidor de desarrollo local con `uvicorn`:

```bash
uvicorn src.main:app --reload
```

O utilizando la CLI de FastAPI:

```bash
fastapi dev src/main.py
```

El servidor quedará disponible en:
- **API Base:** `http://127.0.0.1:8000`
- **Documentación interactiva Swagger UI:** `http://127.0.0.1:8000/docs`
- **Documentación alternativa ReDoc:** `http://127.0.0.1:8000/redoc`

---

## 📖 Endpoints

### 1. Obtener producto por URL
Extrae la información completa de una página de producto individual.

- **Método:** `GET`
- **Ruta:** `/api/v1/item`
- **Parámetros:**
  - `url` (*requerido*): URL del producto en Amazon.

**Ejemplo de respuesta (`200 OK`):**
```json
{
  "name": "Sample Ultralight Laptop 14\" - 16GB RAM, 512GB SSD",
  "price": 749.99,
  "product_details": {
    "batteries": "1 Lithium Polymer batteries required. (included)",
    "package_dimensions": "30.0 x 20.0 x 2.0 cm; 1.3 kg",
    "manufacturer": "SampleBrand",
    "asin": "B000EXAMPLE",
    "country_of_origin": "Spain"
  },
  "url": "https://www.amazon.es/dp/B000EXAMPLE",
  "image": "https://m.media-amazon.com/images/I/sample_product.jpg"
}
```

---

### 2. Buscar productos
Busca artículos por término clave con soporte de paginación.

- **Método:** `GET`
- **Ruta:** `/api/v1/items`
- **Parámetros:**
  - `query` (*requerido*): Término a buscar (ej: `laptop`, `headphones`).
  - `page` (*opcional*, por defecto `'1'`): Número de página.

**Ejemplo de respuesta (`200 OK`):**
```json
[
  {
    "name": "Sample Sports Protein Powder 500g - Unflavored",
    "price": 24.99,
    "product_details": {},
    "url": "https://www.amazon.es/dp/B001EXAMPLE",
    "image": "https://m.media-amazon.com/images/I/sample_search.jpg"
  }
]
```

---

### 3. Respuestas de Error
Si ocurre un fallo en el proceso de scraping, se devuelve una estructura estandarizada:

```json
{
  "type": "parse-error",
  "error": "Product details container div not found (id=\"detailBulletsWrapper_feature_div\")"
}
```

---

## 📁 Estructura del Proyecto

```
amazon-scraper-fastapi/
├── src/
│   ├── main.py                 # Aplicación FastAPI y definición de rutas
│   ├── models/
│   │   └── item.py             # Modelo de datos Pydantic (Item)
│   └── scrappers/
│       ├── amazon_scraper.py   # Lógica de scraping, selectores y sanitización
│       └── scraping_error.py   # Excepción ScrapingError
├── .gitignore                  # Archivos ignorados por git
└── README.md                   # Documentación del proyecto
```
