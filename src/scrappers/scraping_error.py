class ScrapingError(Exception):
    def __init__(self, message: str, *args: str):
        super().__init__(message, *args)