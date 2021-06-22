import queue
import threading
import time
from product import Product
import products_pb2
import logging
from too_good_to_go_client import TooGoodToGoClient


class ProductsQueue():

    def __init__(self, tgtgClient: TooGoodToGoClient):
        self.__InitLogging()
        self.logger.info("ProductsQueue constructor")
        self.queue = queue.Queue()
        self.set = {}
        self.client = tgtgClient
        self.client.AddEventHandler(self.__productsReceivedEventHandler)

    def __iter__(self):
        return self

    def _next(self):
        return self.queue.get()

    def __next__(self):
        return self._next()

    def add_response(self, productId):
        self.queue.put(products_pb2.ProductResponse(id=productId))

    def __productsReceivedEventHandler(self, products: list[Product]):
        for product in products:
            if (product not in self.set): # TODO also check for timestamp
                self.logger.debug(
                f"__productsReceivedEventHandler {product.itemId}")
                self.set #TODO add to set
                self.add_response(product.itemId)

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
