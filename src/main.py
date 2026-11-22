from fastapi import FastAPI
from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.scraping_error import ScrapingError

app = FastAPI()
amazon_scraper = AmazonScraper()

@app.get('/api/v1/item')
def get_item(url: str):
    try:
        return amazon_scraper.get_item(url=url)
    except ScrapingError as exception:
        return {
            'error': exception.args[1],
            'type': exception.args[0]
        }

@app.get('/api/v1/items')
def get_items(query: str, page: str='1'):
    try:
        return amazon_scraper.get_items(query=query, page=page)
    except ScrapingError as exception:
        return {
            'error': exception.args[1],
            'type': exception.args[0]
        }