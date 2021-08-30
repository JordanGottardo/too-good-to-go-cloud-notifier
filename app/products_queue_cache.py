import logging


class ProductsQueueCache():

    def __init__(self):
        self.productsQueueDictionary = {}

    def Add(self, id, productsQueue):
        self.productsQueueDictionary[id] = productsQueue

    def Get(self, id):
        return self.productsQueueDictionary[id]

    def Contains(self, id):
        return id in self.productsQueueDictionary

    def RestartMonitoring(self, id):
        self.productsQueueDictionary[id].RestartMonitoring()

    def SoftStopMonitoring(self, id):
        if id in self.productsQueueDictionary:
            self.productsQueueDictionary[id].SoftStopMonitoring()
        else:
            self.logger.warn(
                f"ProductsQueueCache SoftStopMonitoring: No subscription with {id} ID")

    def HardStopMonitoring(self, id):
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
