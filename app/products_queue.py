import queue
import threading
import time
import products_pb2
import logging
from too_good_to_go_client import TooGoodToGoClient


class ProductsQueue():

    def __init__(self, tgtgClient: TooGoodToGoClient):
        self.__InitLogging()
        self.logger.info("ProductsQueue constructor")
        self.queue = queue.Queue()
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

    def __productsReceivedEventHandler(self, products):
        for product in products:
            self.logger.debug(
                f"__productsReceivedEventHandler {product['item']['item_id']}")
            self.add_response(product['item']['item_id'])

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
