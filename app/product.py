from store import Store
from datetime import datetime

class Product:
    def __init__(self, productFromClient):
        self.id = productFromClient["item"]["item_id"]
        self.price = productFromClient["item"]["price_including_taxes"]["minor_units"]
        self.decimals = productFromClient["item"]["price_including_taxes"]["decimals"]
        self.pickupLocation = productFromClient["pickup_location"]["address"]["address_line"]
        self.isAvailable = productFromClient["items_available"] > 0
        self.store = Store(productFromClient["store"])
        self.createdTime = datetime.now()

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, o):
        return not self.__eq__(o)

    def __hash__(self):
        return hash(self.id)