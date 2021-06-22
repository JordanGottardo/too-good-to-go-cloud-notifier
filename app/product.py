from store import Store

class Product:
    def __init__(self, productFromClient):
        self.itemId = productFromClient["item"]["item_id"]
        self.price = productFromClient["item"]["price"]["minor_units"]
        self.decimals = productFromClient["item"]["price"]["decimals"]
        self.store = Store(productFromClient["store"])