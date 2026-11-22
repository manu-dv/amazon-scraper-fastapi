import re
import time
from random import uniform
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from requests import Session

from src.models.item import Item

from .scraping_error import ScrapingError


class AmazonScraper:
    # Selectores para página de producto individual
    SELECTOR_PRODUCT_TITLE: str = 'productTitle'
    SELECTOR_PRICE_WHOLE: str = 'a-price-whole'
    SELECTOR_PRICE_FRACTION: str = 'a-price-fraction'
    SELECTOR_IMG_CONTAINER: str = 'imgTagWrapperId'
    SELECTOR_DETAILS_WRAPPER: str = 'detailBulletsWrapper_feature_div'
    SELECTOR_DETAILS_BULLETS: str = 'detailBullets_feature_div'
    SELECTOR_BULLET_ITEM: str = 'a-list-item'

    # Selectores para listado de búsqueda
    SELECTOR_LIST_ITEM: str = 'listitem'
    SELECTOR_TITLE_RECIPE: str = 'title-recipe'
    SELECTOR_PRICE_OFFSCREEN: str = 'a-offscreen'
    SELECTOR_SEARCH_IMAGE: str = 's-image'
    SELECTOR_SEARCH_ITEM_LINK: str = 'a-link-normal s-line-clamp-3 s-link-style a-text-normal'

    # Al instanciar el objeto creo una sesión con la cabecera de un navegador
    def __init__(self):
        self._headers: dict[str, str]= {
            'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'),
            'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'),
            'Accept-Language': ('en-US,en;q=0.9,es;q=0.8')
        }

        self._session: Session = requests.Session()
        self._session.headers.update(self._headers)

    @staticmethod
    def _clean_text(text: str) -> str:
        # Elimina marcas unicode de control invisibles (\u200e LTR, \u200f RTL, etc.)
        cleaned = re.sub(r'[\u200e\u200f\u200b-\u200d\ufeff]', '', text)
        # Normaliza espacios y saltos de línea repetidos
        return ' '.join(cleaned.split()).strip()

    @staticmethod
    def _clean_url(url: str) -> str:
        # Decodifica caracteres escapados (%2F, etc.) por si proviene de un enlace patrocinado /sspa/
        decoded_url = unquote(url)
        match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', decoded_url)
        if match:
            return f'https://www.amazon.es/dp/{match.group(1)}'
        return url.split('?')[0] if '?' in url else url

    @staticmethod
    def _clean_image_url(image_url: str | None) -> str | None:
        if not image_url:
            return None
        # Elimina el sufijo de reescalado y compresión de Amazon para obtener máxima resolución
        return re.sub(r'\._[^.]+\.', '.', image_url)
        
    def get_item(self, url: str) -> Item:
        time.sleep(uniform(2, 5))
        response = self._session.get(url=url, timeout=(5, 10))
        
        # En caso de que el status code no sea 200 no continua
        response.raise_for_status()
        
        if 'triggerInterstitialChallenge' in response.text:
            raise ScrapingError('cloudflare-block', 'JavaScript challenge detected (triggerInterstitialChallenge)')
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        product_details_div = soup.find('div', {'id': self.SELECTOR_DETAILS_WRAPPER})
        if product_details_div is None:
            raise ScrapingError('parse-error', f'Product details container div not found (id="{self.SELECTOR_DETAILS_WRAPPER}")')

        product_details_bullets_div = product_details_div.find('div', {'id': self.SELECTOR_DETAILS_BULLETS})
        if product_details_bullets_div is None:
            raise ScrapingError('parse-error', f'Product details bullets div not found (id="{self.SELECTOR_DETAILS_BULLETS}")')

        # Instancio el diccionario y busco todas los detalles, si no tiene continúa con la ejecución
        product_details: dict[str, str] = {}
        product_details_bullets = product_details_bullets_div.find_all('span', {'class': self.SELECTOR_BULLET_ITEM})
        if product_details_bullets:
            for bullet in product_details_bullets:
                cleaned_bullet = self._clean_text(bullet.text)
                if ':' in cleaned_bullet:
                    key, value = cleaned_bullet.split(':', 1)
                    product_details[key.strip().replace(' ', '_').lower()] = value.strip()
                elif cleaned_bullet:
                    product_details[cleaned_bullet] = ''

        image_div = soup.find('div', {'id': self.SELECTOR_IMG_CONTAINER})
        if image_div is None:
            raise ScrapingError('parse-error', f'Image container div not found (id="{self.SELECTOR_IMG_CONTAINER}")')
        
        image_tag = image_div.find('img')
        if image_tag is None:
            raise ScrapingError('parse-error', f'Image <img> tag not found inside div#{self.SELECTOR_IMG_CONTAINER}')
            
        # Formatea la imagen para que sea una cadena de texto limpia en máxima resolución o None
        raw_image_src = image_tag.get('src')
        image: str | None = self._clean_image_url(raw_image_src) if isinstance(raw_image_src, str) else None
        
        name = soup.find('span', {'id': self.SELECTOR_PRODUCT_TITLE})
        integer_price = soup.find('span', {'class': self.SELECTOR_PRICE_WHOLE})
        decimal_price = soup.find('span', {'class': self.SELECTOR_PRICE_FRACTION})
        if name is None or integer_price is None or decimal_price is None:
            raise ScrapingError('parse-error', f'Required product fields missing (productTitle: id="{self.SELECTOR_PRODUCT_TITLE}", price: class="{self.SELECTOR_PRICE_WHOLE}" / "{self.SELECTOR_PRICE_FRACTION}")')
        
        # Formateo los datos y devuelvo el Item encontrado o lanzo un error personalizado
        name = name.text.strip()
        integer_price = integer_price.text.strip()
        decimal_price = decimal_price.text.strip()
        price = float(f'{integer_price}{decimal_price}'.replace(',', '.'))
        clean_url = self._clean_url(url)
        
        return Item(name=name, price=price, product_details=product_details, url=clean_url, image=image)
            
    def get_items(self, query: str, page: str) -> list[Item]:
        format_query = query.replace(' ', '+')
        url = f'https://www.amazon.es/s?k={format_query}&page={page}'
        
        time.sleep(uniform(2,5))

        response = self._session.get(url=url, timeout=(5, 10))
        
        response.raise_for_status()
        
        if 'triggerInterstitialChallenge' in response.text:
            raise ScrapingError('cloudflare-block', 'JavaScript challenge detected (triggerInterstitialChallenge)')
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        item_list: list[Item] = []
        div_list = soup.find_all('div', {'role': self.SELECTOR_LIST_ITEM})
        
        if div_list:
            for div in div_list:
                image = None
                
                name_div = div.find('div', {'data-cy': self.SELECTOR_TITLE_RECIPE})
                if name_div is None:
                    continue

                name_h2 = name_div.find('h2')
                if name_h2 is None:
                    continue

                name_next_h2 = name_h2.find_next('h2')
                if name_next_h2 is None:
                    continue

                name_span = name_next_h2.find('span')
                price_span = div.find('span', {'class': self.SELECTOR_PRICE_OFFSCREEN})
                image_element = div.find('img', {'class': self.SELECTOR_SEARCH_IMAGE})
                item_url_a = div.find('a', {'class': self.SELECTOR_SEARCH_ITEM_LINK})
            
                if name_span is None or price_span is None:
                    continue
                        
                name: str = name_span.text.strip()
                price: float = float(price_span.text.strip().replace('€', ''))
                # Formatea la imagen para que sea una cadena de texto limpia en máxima resolución o None
                raw_image_src = image_element.get('src') if image_element else None
                image: str | None = self._clean_image_url(raw_image_src) if isinstance(raw_image_src, str) else None
                raw_item_url: str = f'https://www.amazon.es{item_url_a['href']}' if item_url_a else 'Unknown'
                item_url: str = self._clean_url(raw_item_url) if item_url_a else 'Unknown'
                
                item_list.append(Item(
                    name=name,
                    price=price,
                    image=image,
                    url=item_url
                ))
                
            return item_list
        
        raise ScrapingError('no-results', f'No items container div[role="{self.SELECTOR_LIST_ITEM}"] found for URL: {url}')
            
        