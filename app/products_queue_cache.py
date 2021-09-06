import logging
from threading import RLock


class ProductsQueueCache():

    def __init__(self):
        self.lock = RLock()
        self.productsQueueDictionary = {}
        self.__InitLogging()

    def Add(self, id, productsQueue):
        with self.lock:
            self.productsQueueDictionary[id] = productsQueue

    def Get(self, id):
        with self.lock:
            return self.productsQueueDictionary[id]

    def Contains(self, id):
        with self.lock:
            return id in self.productsQueueDictionary

    def RestartMonitoring(self, id):
        with self.lock:
            if self.Contains(id):
                self.productsQueueDictionary[id].RestartMonitoring()
            else:
                self.logger.warn(
                    f"ProductsQueueCache RestartMonitoring: No subscription with {id} ID")

    def SoftStopMonitoring(self, id):
        with self.lock:
            if self.Contains(id):
                self.productsQueueDictionary[id].SoftStopMonitoring()
            else:
                self.logger.warn(
                    f"ProductsQueueCache SoftStopMonitoring: No subscription with {id} ID")

    def HardStopMonitoring(self, id):
        with self.lock:
            if self.Contains(id):
                self.productsQueueDictionary[id].HardStopMonitoring()
                self.productsQueueDictionary.pop(id)
            else:
                self.logger.warn(
                    f"ProductsQueueCache HardStopMonitoring: No subscription with {id} ID")

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueueCache")
        self.logger.setLevel(logging.DEBUG)
