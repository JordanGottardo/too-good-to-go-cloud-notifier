from tgtg import TgtgClient
from event import Event
from product import Product
import threading
import logging


class TooGoodToGoClient:

    def __init__(self, email, password):
        self.__InitLogging()

        self.logger.info(
            f"TooGoodToGoClient Constructor: initializing for user {email}")

        self.email = email
        self.password = password
        self.client = TgtgClient(email=email, password=password)
        self.event = Event()
        self.monitoringStopped = False

    def AddEventHandler(self, eventHandler):
        self.event.append(eventHandler)

    def StartMonitor(self):
        self.__GetProductsPeriodically()

    def StopMonitor(self):
        self.logger.debug("TooGoodToGoClient: StopMonitor")
        self.monitoringStopped = True
        self.timer.cancel()

    def __GetProducts(self):
        return self.__ToAvailableProducts(self.client.get_items())

    def __GetProductsPeriodically(self):
        if (not self.monitoringStopped):
            self.timer = threading.Timer(30, self.__GetProductsPeriodically)
            self.timer.daemon = True
            self.timer.start()
            self.event(self.__GetProducts())

    def __ToAvailableProducts(self, productsFromClient: list):
        availableProducts = list(
            filter(lambda product: product["items_available"] > 0, productsFromClient))

        self.logger.debug(
            f"TooGoodToGoClient retrieved {len(productsFromClient)} favorite products, {len(availableProducts)} of which are available")

        return map(lambda product: Product(product), productsFromClient)

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("TooGoodToGoClient")
        self.logger.setLevel(logging.DEBUG)
