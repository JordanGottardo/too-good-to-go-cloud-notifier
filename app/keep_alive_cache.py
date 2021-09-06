import threading
import logging
from datetime import datetime

from products_queue_cache import ProductsQueueCache
from abc import ABC, abstractmethod


class KeepAliveCacheBase(ABC):

    def __init__(self, productsQueueCache):
        self.__InitLogging()
        self.keepAliveDictionary = {}
        self.productsQueueCache: ProductsQueueCache = productsQueueCache
        self.lock = threading.RLock()
        self.stopSubscriptionStaleTimer = False

    @property
    @abstractmethod
    def SubscriptionStaleTimeoutSeconds(self):
        pass

    @property
    @abstractmethod
    def ClassNameForLogging(self):
        pass

    @abstractmethod
    def Stop(self, identifier):
        pass

    def AddOrUpdate(self, id, timestamp):
        with self.lock:
            prevKeepAliveDictionaryLength = len(self.keepAliveDictionary)
            self.keepAliveDictionary[id] = timestamp
            if prevKeepAliveDictionaryLength == 0:
                self.logger.debug(
                    f"{self.ClassNameForLogging}: Starting subscription stale removal timer")
                self.stopSubscriptionStaleTimer = False
                self.__StartStoppingStaleSubscriptionsTimer()

    def __StartStoppingStaleSubscriptionsTimer(self):
        if (not self.stopSubscriptionStaleTimer):
            timer = threading.Timer(
                30, self.__StartStoppingStaleSubscriptionsTimer)
            timer.daemon = True
            timer.start()
            identifiersToRemove = []

            with self.lock:
                for identifier, timestamp in self.keepAliveDictionary.items():
                    if self.__IsSubscriptionStale(timestamp):
                        self.logger.debug(
                            f"{self.ClassNameForLogging}: Removing stale subscription {identifier}")
                        identifiersToRemove.append(identifier)
                        self.Stop(identifier)
                self.__RemoveTimestampsForRemovedSubscriptions(identifiersToRemove)

    def __RemoveTimestampsForRemovedSubscriptions(self, identifiersToRemove):
        for id in identifiersToRemove:
            self.keepAliveDictionary.pop(id)
        if (len(self.keepAliveDictionary) == 0):
            self.stopSubscriptionStaleTimer = True

    def __IsSubscriptionStale(self, lastKeepAliveTimestamp):
        return self.__SecondsDifferenceBetween(lastKeepAliveTimestamp, datetime.now()) > self.SubscriptionStaleTimeoutSeconds

    def __SecondsDifferenceBetween(self, olderDate: datetime, newerDate: datetime):
        seconds = (newerDate - olderDate).total_seconds()
        return seconds

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger(self.ClassNameForLogging)
        self.logger.setLevel(logging.DEBUG)

class ShortLivedKeepAliveCache(KeepAliveCacheBase):
    SubscriptionStaleTimeoutSeconds = 60

    ClassNameForLogging = "ShortLivedKeepAliveCache"

    def Stop(self, identifier):
        self.productsQueueCache.SoftStopMonitoring(identifier)

class LongLivedKeepAliveCache(KeepAliveCacheBase):
    SubscriptionStaleTimeoutSeconds = 60 * 60 * 24

    ClassNameForLogging = "LongLivedKeepAliveCache"

    def Stop(self, identifier):
        self.productsQueueCache.HardStopMonitoring(identifier)