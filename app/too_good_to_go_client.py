from tgtg import TgtgClient
from event import Event
import threading


class TooGoodToGoClient:

    def __init__(self, email, password):
        print(
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
        print("__GetProductsPeriodically")
        timer = threading.Timer(30, self.__GetProductsPeriodically)
        timer.daemon = True
        timer.start()
        self.event(self.__GetProducts())
