import threading
import logging
from datetime import datetime

from products_queue_cache import ProductsQueueCache


class KeepAliveCache():

    def __init__(self, productsQueueCache):
        self.__InitLogging()
        self.keepAliveDictionary = {}
        self.productsQueueCache: ProductsQueueCache = productsQueueCache
        self.lock = threading.Lock()
        self.stopSubscriptionStaleTimer = False

    def AddOrUpdate(self, id, timestamp):
        prevKeepAliveDictionaryLength = len(self.keepAliveDictionary)
        self.keepAliveDictionary[id] = timestamp
        if prevKeepAliveDictionaryLength == 0:
            self.logger.debug(
                "KeepAliveCache: Starting subscription stale removal timer")
            self.stopSubscriptionStaleTimer = False
            self.__StartStoppingStaleSubscriptions()

    def __StartStoppingStaleSubscriptions(self):
        if (not self.stopSubscriptionStaleTimer):
            timer = threading.Timer(
                30, self.__StartStoppingStaleSubscriptions)
            timer.daemon = True
            timer.start()
            identifiersToRemove = []

            for identifier, timestamp in self.keepAliveDictionary.items():
                if self.__IsSubscriptionStale(timestamp):
                    self.logger.debug(
                        f"Removing stale subscription {identifier}")
                    identifiersToRemove.append(identifier)
                    self.productsQueueCache.Get(
                        identifier).StopMonitoring()
            self.__RemoveTimestampsForRemovedSubscriptions(
                identifiersToRemove)

    def __RemoveTimestampsForRemovedSubscriptions(self, identifiersToRemove):
        for id in identifiersToRemove:
            self.keepAliveDictionary.pop(id)
        if (len(self.keepAliveDictionary) == 0):
            self.stopSubscriptionStaleTimer = True

    def __IsSubscriptionStale(self, lastKeepAliveTimestamp):
        return self.__SecondsDifferenceBetween(lastKeepAliveTimestamp, datetime.now()) > 60

    def __SecondsDifferenceBetween(self, olderDate: datetime, newerDate: datetime):
        seconds = (newerDate - olderDate).total_seconds()
        return seconds

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("KeepAliveCache")
        self.logger.setLevel(logging.DEBUG)
