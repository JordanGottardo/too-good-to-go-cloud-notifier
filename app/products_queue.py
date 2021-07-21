import queue
import threading
from product import Product, Store
from products_pb2 import ProductServerMessage, ProductResponse, Store, KeepAlive
import logging
from too_good_to_go_client import TooGoodToGoClient
from datetime import datetime
import os


class ProductsQueue():

    def __init__(self, tgtgClient: TooGoodToGoClient):
        self.__InitLogging()
        self.logger.info("ProductsQueue constructor")
        self.productsLock = threading.Lock()
        self.keepAliveLock = threading.Lock()
        self.queueContainsKeepAlive = False
        self.monitoringStopped = False
        self.productsIdAndKeepaliveQueue = queue.Queue()
        self.productsDictionary = {}
        self.productsStaleDictionary = {}
        self.client = tgtgClient
        self.PRODUCT_STALE_INTERVAL_HOURS = int(
            os.environ["PRODUCT_STALE_INTERVAL_HOURS"])
        self.PRODUCTS_QUEUE_CLEANUP_INTERVAL_DAYS = int(
            os.environ["PRODUCTS_QUEUE_CLEANUP_INTERVAL_DAYS"])
        self.client.AddEventHandler(self.__productsReceivedEventHandler)
        self.__StartPeriodicCleanUpTask()
        self.__StartHeartBeatTask()

    def __iter__(self):
        return self

    def __next__(self):
        return self.__next()

    def StopMonitoring(self):
        self.monitoringStopped = True
        self.client.StopMonitor()

    def __next(self):
        self.logger.debug(
            f"There are {self.__GetProductIdQueueLength()} items in queue")

        productIdOrKeepalive = self.productsIdAndKeepaliveQueue.get()

        if (self.monitoringStopped):
            return

        with self.keepAliveLock:
            if (type(productIdOrKeepalive) is ProductServerMessage):
                self.queueContainsKeepAlive = False
                return productIdOrKeepalive

        productId: str = productIdOrKeepalive
        if (not productId in self.productsDictionary):
            return self.__next()

        product: Product = self.productsDictionary.pop(productId)
        productForStalenessCheck: Product = self.productsStaleDictionary[productId]

        if (self.__IsProductInfoStale(productForStalenessCheck)):
            self.logger.debug(
                f"Iterator next: product {productId} is stale: removing it")
            self.productsStaleDictionary.pop(productId)
        return self.__ToProductResponseServerMessage(product)

    def __ToProductResponseServerMessage(self, product: Product):
        serverMessage = ProductServerMessage()
        productResponse = ProductResponse(
            id=product.id,
            price=product.price,
            decimals=product.decimals,
            pickupLocation=product.pickupLocation,
            store=self.__ToStore(product.store)
        )

        serverMessage.productResponse.CopyFrom(productResponse)

        return serverMessage

    def __ToStore(self, store: Store):
        return (Store(
            name=store.name,
            address=store.address,
            city=store.city
        ))

    def __productsReceivedEventHandler(self, products: list[Product]):
        with self.productsLock:
            self.logger.debug(f"ProductsQueue __productsReceivedEventHandler")
            toBeInsertedInQueue = []
            toBeRemovedFromQueue = []

            for product in products:
                productId = product.id
                productAlreadySeen = productId in self.productsStaleDictionary

                if (product.isAvailable):
                    self.productsDictionary[productId] = product
                    if (not productAlreadySeen):
                        self.logger.debug(
                            f"New available product with ID {productId} received: inserting")
                        self.productsStaleDictionary[productId] = product
                        toBeInsertedInQueue.append(productId)
                    elif (self.__IsProductInfoStale(self.productsStaleDictionary[productId])):
                        self.logger.debug(
                            f"Available product {productId} {product.pickupLocation} is stale: updating it")
                        toBeInsertedInQueue.append(productId)
                        self.productsStaleDictionary.pop(productId)
                        self.productsStaleDictionary[productId] = product
                else:
                    toBeRemovedFromQueue.append(productId)

            self.__AddProductsToQueue(toBeInsertedInQueue)
            self.__RemoveProductsFromQueue(toBeRemovedFromQueue)

    def __IsProductInfoStale(self, product: Product):
        return self.__HoursDifferenceBetween(product.createdTime, datetime.now()) > self.PRODUCT_STALE_INTERVAL_HOURS

    def __HoursDifferenceBetween(self, olderDate: datetime, newerDate: datetime):
        return (newerDate - olderDate).total_seconds() / (60 * 60)

    def __AddProductsToQueue(self, productsIdToInsert: list):
        for id in productsIdToInsert:
            self.productsIdAndKeepaliveQueue.put(id)

    def __RemoveProductsFromQueue(self, productsIdToRemove: list):
        for id in productsIdToRemove:
            if (id in self.productsDictionary):
                self.logger.debug(
                    f"Formerly available product is no longer available: removing {id} from queue")
                self.productsDictionary.pop(id)
            if (id in self.productsStaleDictionary):
                self.productsStaleDictionary.pop(id)

    def __StartPeriodicCleanUpTask(self):
        self.__PeriodicCleanUpTask()

    def __PeriodicCleanUpTask(self):
        self.logger.debug(
            f"ProductsQueue __PeriodicCleanUpTask: found {self.__GetProductIdQueueLength()} products in queue, removing all of them")
        timer = threading.Timer(
            self._GetQueueCleanupIntervalSeconds(), self.__PeriodicCleanUpTask)
        timer.daemon = True
        timer.start()
        with self.productsLock:
            with self.keepAliveLock:
                with self.productsIdAndKeepaliveQueue.mutex:
                    self.productsIdAndKeepaliveQueue.queue.clear()
                    self.queueContainsKeepAlive = False

    def __StartHeartBeatTask(self):
        self.__HeartBeatTask()

    def __HeartBeatTask(self):
        timer = threading.Timer(20, self.__HeartBeatTask)
        timer.daemon = True
        timer.start()
        with self.keepAliveLock:
            if (not self.queueContainsKeepAlive):
                self.logger.debug("Adding keepAlive to queue")
                self.queueContainsKeepAlive = True
                productServerMessage = ProductServerMessage()
                productServerMessage.keepAlive.CopyFrom(KeepAlive())
                self.productsIdAndKeepaliveQueue.put(productServerMessage)

    def __GetProductIdQueueLength(self):
        return str(self.productsIdAndKeepaliveQueue.qsize())

    def _GetQueueCleanupIntervalSeconds(self):
        return self.PRODUCTS_QUEUE_CLEANUP_INTERVAL_DAYS * 60 * 60

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
