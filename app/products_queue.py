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
        self.productsLock = threading.RLock()
        self.keepAliveLock = threading.RLock()
        self.queueContainsKeepAlive = False
        self.monitoringStopped = False
        self.productsIdAndKeepaliveQueue = queue.Queue()
        self.productsDictionary = {}
        self.productsStaleDictionary = {}
        self.client = tgtgClient
        if ("PRODUCT_STALE_INTERVAL_HOURS" in os.environ):
            self.PRODUCT_STALE_INTERVAL_HOURS = int(
                os.environ["PRODUCT_STALE_INTERVAL_HOURS"])
        else:
            self.PRODUCT_STALE_INTERVAL_HOURS = 24

        if ("PRODUCTS_QUEUE_CLEANUP_INTERVAL_DAYS" in os.environ):
            self.PRODUCTS_QUEUE_CLEANUP_INTERVAL_DAYS = int(
                os.environ["PRODUCTS_QUEUE_CLEANUP_INTERVAL_DAYS"])
        else:
            self.PRODUCTS_QUEUE_CLEANUP_INTERVAL_DAYS = 1

        self.client.AddEventHandler(self.__productsReceivedEventHandler)
        self.__StartPeriodicCleanUpTask()
        self.__StartHeartBeatTask()

    def __iter__(self):
        return self

    def __next__(self):
        return self.__next()

    def StartMonitoring(self):
        self.logger.debug("ProductsQueue StartMonitoring")
        self.client.StartMonitor()

    def RestartMonitoring(self):
        self.logger.debug("ProductsQueue RestartMonitoring")
        self.monitoringStopped = False
        self.productsIdAndKeepaliveQueue.put(self.__AKeepAliveMessage())

    def HardStopMonitoring(self):
        with self.keepAliveLock:
            self.logger.debug("ProductsQueue HardStopMonitoring")
            self.periodicalCleanUpTimer.cancel()
            self.keepAliveTimer.cancel()
            self.monitoringStopped = True
            self.client.StopMonitor()
            self.productsIdAndKeepaliveQueue.put(self.__AKeepAliveMessage())

    def SoftStopMonitoring(self):
        with self.keepAliveLock:
            self.logger.debug("ProductsQueue SoftStopMonitoring")
            self.monitoringStopped = True
            self.productsIdAndKeepaliveQueue.put(self.__AKeepAliveMessage())

    def __next(self):
        self.logger.debug(
            f"ProductsQueue There are {self.__GetProductIdQueueLength()} items in queue")

        productIdOrKeepalive = self.productsIdAndKeepaliveQueue.get()

        if (self.monitoringStopped):
            raise StopIteration()

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
                f"ProductsQueue Iterator next: product {productId} is stale: removing it")
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
            toBeInsertedInQueue = []
            toBeRemovedFromQueue = []

            for product in products:
                productId = product.id
                productAlreadySeen = productId in self.productsStaleDictionary

                if (product.isAvailable):
                    self.productsDictionary[productId] = product
                    if (not productAlreadySeen):
                        self.logger.debug(
                            f"ProductsQueue: New available product with ID {productId} received: inserting")
                        self.productsStaleDictionary[productId] = product
                        toBeInsertedInQueue.append(productId)
                    elif (self.__IsProductInfoStale(self.productsStaleDictionary[productId])):
                        self.logger.debug(
                            f"ProductsQueue: Available product {productId} {product.store.name} is stale: updating it")
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
                    f"ProductsQueue: Formerly available product is no longer available: removing {id} from queue")
                self.productsDictionary.pop(id)
            if (id in self.productsStaleDictionary):
                self.productsStaleDictionary.pop(id)

    def __StartPeriodicCleanUpTask(self):
        self.__PeriodicCleanUpTask()

    def __PeriodicCleanUpTask(self):
        self.logger.debug(
            f"ProductsQueue __PeriodicCleanUpTask: found {self.__GetProductIdQueueLength()} products in queue, removing all of them")
        self.periodicalCleanUpTimer = threading.Timer(
            self._GetQueueCleanupIntervalSeconds(), self.__PeriodicCleanUpTask)
        self.periodicalCleanUpTimer.daemon = True
        self.periodicalCleanUpTimer.start()
        with self.productsLock:
            with self.keepAliveLock:
                with self.productsIdAndKeepaliveQueue.mutex:
                    self.productsIdAndKeepaliveQueue.queue.clear()
                    self.queueContainsKeepAlive = False

    def __StartHeartBeatTask(self):
        self.__HeartBeatTask()

    def __HeartBeatTask(self):
        self.keepAliveTimer = threading.Timer(20, self.__HeartBeatTask)
        self.keepAliveTimer.daemon = True
        self.keepAliveTimer.start()
        with self.keepAliveLock:
            if (not self.queueContainsKeepAlive):
                self.logger.debug("ProductsQueue Adding keepAlive to queue")
                self.queueContainsKeepAlive = True
                self.productsIdAndKeepaliveQueue.put(
                    self.__AKeepAliveMessage())

    def __GetProductIdQueueLength(self):
        return str(self.productsIdAndKeepaliveQueue.qsize())

    def _GetQueueCleanupIntervalSeconds(self):
        return self.PRODUCTS_QUEUE_CLEANUP_INTERVAL_DAYS * 24 * 60 * 60

    def __AKeepAliveMessage(self):
        productServerMessage = ProductServerMessage()
        productServerMessage.keepAlive.CopyFrom(KeepAlive())
        return productServerMessage

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
