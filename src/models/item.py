from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: float
    product_details: dict[str, str] = {}
    url: str = ''
    image: str | None = 'https://commons.wikimedia.org/wiki/File:Image-not-found.png'