from tgtg import TgtgClient
from event import Event
import threading
import logging


class TooGoodToGoClient:

    def __init__(self, email, password):
        self.__InitLogging()

        self.logger.info(
            f"TooGoodToGoClient Constructor: initializing for user {email} with password {password}")

        self.email = email
        self.password = password
        self.client = TgtgClient(email=email, password=password)
        self.event = Event()

    def AddEventHandler(self, eventHandler):
        self.event.append(eventHandler)

    def StartMonitor(self):
        self.__GetProductsPeriodically()

    def __GetProducts(self):
        return self.client.get_items()

    def __GetProductsPeriodically(self):
        self.logger.debug("TooGoodToGoClient timer ticked: getting products")
        timer = threading.Timer(30, self.__GetProductsPeriodically)
        timer.daemon = True
        timer.start()
        self.event(self.__GetProducts())

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("TooGoodToGoClient")
        self.logger.setLevel(logging.DEBUG)
