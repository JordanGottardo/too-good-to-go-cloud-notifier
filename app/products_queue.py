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
        self.productsIdQueue = queue.Queue()
        self.productsDictionary = {}
        self.productsStaleDictionary = {}
        self.client = tgtgClient
        self.client.AddEventHandler(self.__productsReceivedEventHandler)

    def __iter__(self):
        return self

    def _next(self):
        productId: str = self.productsIdQueue.get()
        product: Product = self.productsDictionary.pop(productId)
        productForStalenessCheck: Product = self.productsStaleDictionary[productId]

        if (self.__IsProductInfoStale(productForStalenessCheck)):
            self.logger.debug(
                f"Iterator next: product {productId} is stale: removing it")
            self.productsDictionary.pop(productId)
        return self.__ToProductResponse(product)

    def __next__(self):
        return self._next()

    def __ToProductResponse(self, product: Product):
        return (products_pb2.ProductResponse(id=product.id))

    def __productsReceivedEventHandler(self, products: list[Product]):
        for product in products:
            productId = product.id
            self.productsDictionary[productId] = product
            productAlreadySeen = productId in self.productsStaleDictionary

            if (not productAlreadySeen):
                self.logger.debug(
                    f"New product with {productId} received: inserting")
                self.productsStaleDictionary[productId] = product
                self.productsIdQueue.put(productId)
            elif (self.__IsProductInfoStale(self.productsStaleDictionary[productId])):
                self.logger.debug(f"Product {productId} is stale: updating it")
                self.productsIdQueue.put(productId)
                self.productsStaleDictionary.pop(productId)
                self.productsStaleDictionary[productId] = product

    def __IsProductInfoStale(self, product: Product):
        return self.__HoursDifferenceBetween(product.createdTime, datetime.now()) > 2

    def __HoursDifferenceBetween(self, olderDate: datetime, newerDate: datetime):
        minutes = (newerDate - olderDate).total_seconds() / 60
        self.logger.debug(f"time difference is{minutes}")
        return minutes

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
