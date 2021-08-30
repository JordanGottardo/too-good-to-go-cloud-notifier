import logging
from threading import Lock


class ProductsQueueCache():

    def __init__(self):
        self.lock = Lock()
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
            self.productsQueueDictionary[id].RestartMonitoring()

    def SoftStopMonitoring(self, id):
        with self.lock:
            if id in self.productsQueueDictionary:
                self.productsQueueDictionary[id].SoftStopMonitoring()
            else:
                self.logger.warn(
                    f"ProductsQueueCache SoftStopMonitoring: No subscription with {id} ID")

    def HardStopMonitoring(self, id):
        with self.lock:
            if id in self.productsQueueDictionary:
                self.productsQueueDictionary[id].HardStopMonitoring()
                self.productsQueueDictionary.pop(id)
            else:
                self.logger.warn(
                    f"ProductsQueueCache HardStopMonitoring: No subscription with {id} ID")

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueueCache")
        self.logger.setLevel(logging.DEBUG)
