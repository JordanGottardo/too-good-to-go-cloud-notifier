import queue
import threading
import time
from product import Product
import products_pb2
import logging
from too_good_to_go_client import TooGoodToGoClient
from datetime import datetime


class ProductsQueue():

    def __init__(self, tgtgClient: TooGoodToGoClient):
        self.__InitLogging()
        self.logger.info("ProductsQueue constructor")
        self.queue = queue.Queue()
        self.set = set()
        self.client = tgtgClient
        self.client.AddEventHandler(self.__productsReceivedEventHandler)

    def __iter__(self):
        return self

    def _next(self):
        product: Product = self.queue.get()
        return self.__ToProductResponse(product)

    def __next__(self):
        return self._next()

    def __ToProductResponse(self, product: Product):
        return (products_pb2.ProductResponse(id=product.id))

    def __productsReceivedEventHandler(self, products: list[Product]):
        for product in products:
            productAlreadyInSet = product in self.set
            if (not productAlreadyInSet or self.__HoursDifferenceBetween(product.createdTime, datetime.now()) > 1):
                self.logger.debug(
                    f"__productsReceivedEventHandler {product.id}")
                if (productAlreadyInSet):
                    self.set.remove(product)
                self.set.add(product)
                self.queue.put(product)

    def __HoursDifferenceBetween(self, olderDate: datetime, newerDate: datetime):
        minutes = (newerDate - olderDate).total_seconds() / 60
        self.logger.debug(f"time difference is{minutes}")
        return minutes

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
