from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: float
    product_details: dict[str, str] = {}
    url: str = ''
    image: str | None = 'https://upload.wikimedia.org/wikipedia/commons/a/a3/Image-not-found.png?_=20210521171500'