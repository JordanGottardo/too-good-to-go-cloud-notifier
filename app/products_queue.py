import queue
import threading
import time
from product import Product, Store
import products_pb2
import logging
from too_good_to_go_client import TooGoodToGoClient
from datetime import datetime


class ProductsQueue():

    def __init__(self, tgtgClient: TooGoodToGoClient):
        self.__InitLogging()
        self.logger.info("ProductsQueue constructor")
        self.lock = threading.Lock()
        self.productsIdQueue = queue.Queue()
        self.productsDictionary = {}
        self.productsStaleDictionary = {}
        self.client = tgtgClient
        self.client.AddEventHandler(self.__productsReceivedEventHandler)
        self.__StartPeriodicCleanUpTask()

    def __iter__(self):
        return self

    def _next(self):
        self.logger.debug(
            f"There are {self.__GetProductIdQueueLength()} product in queue")
        productId: str = self.productsIdQueue.get()
        if (not productId in self.productsDictionary):
            return self._next()

        product: Product = self.productsDictionary.pop(productId)
        productForStalenessCheck: Product = self.productsStaleDictionary[productId]

        if (self.__IsProductInfoStale(productForStalenessCheck)):
            self.logger.debug(
                f"Iterator next: product {productId} is stale: removing it")
            self.productsStaleDictionary.pop(productId)
        return self.__ToProductResponse(product)

    def __next__(self):
        return self._next()

    def __ToProductResponse(self, product: Product):
        return (products_pb2.ProductResponse(
            id=product.id,
            price=product.price,
            decimals=product.decimals,
            pickupLocation=product.pickupLocation,
            store=self.__ToStore(product.store)
            ))

    def __ToStore(self, store: Store):
        return (products_pb2.Store(
            name=store.name,
            address=store.address,
            city=store.city
        ))

    def __productsReceivedEventHandler(self, products: list[Product]):
        with self.lock:
            self.logger.debug(f"ProductsQueue __productsReceivedEventHandler")
            toBeInsertedInQueue = []

            for product in products:
                productId = product.id
                self.productsDictionary[productId] = product
                productAlreadySeen = productId in self.productsStaleDictionary

                if (not productAlreadySeen):
                    self.logger.debug(
                        f"New product with ID {productId} received: inserting")
                    self.productsStaleDictionary[productId] = product
                    toBeInsertedInQueue.append(productId)
                elif (self.__IsProductInfoStale(self.productsStaleDictionary[productId])):
                    self.logger.debug(f"Product {productId} is stale: updating it")
                    toBeInsertedInQueue.append(productId)
                    self.productsStaleDictionary.pop(productId)
                    self.productsStaleDictionary[productId] = product

            self.__AddProductsToQueue(toBeInsertedInQueue)

    def __IsProductInfoStale(self, product: Product):
        # TODO set condition to less time to receive more notifications
        return self.__HoursDifferenceBetween(product.createdTime, datetime.now()) > 60 * 12

    def __HoursDifferenceBetween(self, olderDate: datetime, newerDate: datetime):
        return (newerDate - olderDate).total_seconds() / 60

    def __AddProductsToQueue(self, productsIdToInsert: list):
        for id in productsIdToInsert:
            self.productsIdQueue.put(id)

    def __StartPeriodicCleanUpTask(self):
        self.__PeriodicCleanUpTask()

    def __PeriodicCleanUpTask(self):
        self.logger.debug(
            f"ProductsQueue __PeriodicCleanUpTask: found {self.__GetProductIdQueueLength()} products in queue, removing all of them")
        # Executes cleanup periodically. TODO: changed to like 5 days
        # timer = threading.Timer(5 * 24 * 60 * 60, self.__PeriodicCleanUpTask)
        timer = threading.Timer(24 * 60 * 60, self.__PeriodicCleanUpTask)
        timer.daemon = True
        timer.start()
        with self.lock:
            with self.productsIdQueue.mutex:
                self.productsIdQueue.queue.clear()

    def __GetProductIdQueueLength(self):
        return str(self.productsIdQueue.qsize())

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
