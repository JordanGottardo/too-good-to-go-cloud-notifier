import queue
import threading
import time
import products_pb2
import logging


class ProductsQueue():

    def __init__(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("ProductsQueue constructor")
        self.queue = queue.Queue()

    def __iter__(self):
        self.logger.debug("Iter")
        return self

    def _next(self):
        self.logger.debug("_next")
        return self.queue.get()

    def __next__(self):
        self.logger.debug("__next__")
        return self._next()

    def add_response(self, productId):
        self.logger.debug("add_response")
        self.queue.put(products_pb2.ProductResponse(id=productId))

    def __addTest(self):
        self.logger.debug("Sleeping for 10 sec")
        print(threading.get_ident())
        time.sleep(10)
        self.add_response("123")
        time.sleep(5)
        self.add_response("456")
        time.sleep(5)
        self.add_response("789")

    def startAdd(self):
        self.logger.debug("StartAdd")
        print(threading.get_ident())
        self.t = threading.Thread(target=self.__addTest, daemon=True)
        self.t.start()

    # def __init__(self):
    #     print("ProductsQueue constructor")
    #     self.queue = queue.Queue()
    #     self.t = threading.Thread(target=self.__threadTest, daemon=True)
    #     self.t.run()

    # def __threadTest(self):
    #     print("Sleeping for 2 sec")
    #     time.sleep(10)
    #     print("Slept for 2 sec, adding to queue")
    #     self.queue.put(products_pb2.ProductResponse(id="123"))
    #     time.sleep(5)
    #     self.queue.put(products_pb2.ProductResponse(id="456"))
    #     time.sleep(5)
    #     self.queue.put(products_pb2.ProductResponse(id="789"))

    # def get(self):
    #     print("Getting item from queue")
    #     yield self.queue.get()
