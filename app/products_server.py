from concurrent import futures
from datetime import datetime
import logging
from keep_alive_cache import KeepAliveCache
from products_queue_cache import ProductsQueueCache
from too_good_to_go_client import TooGoodToGoClient
from products_queue import ProductsQueue
import grpc
from products_pb2_grpc import ProductsManagerServicer, add_ProductsManagerServicer_to_server
from products_pb2 import ProductRequest
import random
import uuid
import threading


class ProductsServicer(ProductsManagerServicer):

    def __init__(self, productsQueueCache: ProductsQueueCache, keepAliveCache: KeepAliveCache):
        self.__InitLogging()
        self.logger.info("ProductsServicer constructor")
        self.productsQueueCache = productsQueueCache
        self.keepAliveCache = keepAliveCache

    def GetProducts(self, requestIterator, context):
        identifier = uuid.uuid4()
        productRequest = next(requestIterator).productRequest
        self.logger.info(
            f"Received request for user {productRequest.username}, ID {identifier}")

        client = TooGoodToGoClient(
            productRequest.username, productRequest.password)
        client.StartMonitor()
        productsQueue = ProductsQueue(client)

        def __GrpcChannelClosedCallback():
            self.logger.debug(
                f"GRPC channel has been closed from client, ID {identifier}")
            productsQueue.StopMonitoring()

        context.add_callback(__GrpcChannelClosedCallback)

        self.productsQueueCache.Add(identifier, productsQueue)
        self.__StartReceivingKeepAlivesAsync(requestIterator, identifier)

        for item in productsQueue:
            if (item.HasField("keepAlive")):
                self.logger.debug(f"Sending KeepAlive, ID {identifier}")
            else:
                self.logger.debug(
                    f"Gotten {item.productResponse.id} {item.productResponse.store.name} from queue. Returning it to the client. ID {identifier}")
            yield item
            
        self.logger.debug(
            f"Monitoring ended for user {productRequest.username}, ID {identifier}")

    def __StartReceivingKeepAlivesAsync(self, requestIterator, identifier):
        thread = threading.Thread(
            target=self.__StartReceivingKeepAlives, args=(requestIterator, identifier))
        thread.daemon = True
        thread.start()

    def __StartReceivingKeepAlives(self, requestIterator, identifier):
        try:
            for request in requestIterator:
                if (request.HasField("keepAlive")):
                    self.logger.debug(
                        f"Received KeepAlive from client {identifier}")
                    self.keepAliveCache.AddOrUpdate(identifier, datetime.now())
                else:
                    self.logger.debug(
                        f"Unknown request received from client {identifier}")
        except:
            self.logger.debug("Error while reading keepAlives from client")

    def __InitLogging(self):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsServicer")
        self.logger.setLevel(logging.DEBUG)


def serve():
    print("Serve")
    options = [
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
        ('grpc.http2.min_time_between_pings_ms', 10000),
        ('grpc.http2.min_ping_interval_without_data_ms', 5000),
    ]
    server = grpc.server(futures.ThreadPoolExecutor(
        max_workers=10), options=options)
    productsQueueCache = ProductsQueueCache()
    keepAliveCache = KeepAliveCache(productsQueueCache)

    add_ProductsManagerServicer_to_server(
        ProductsServicer(productsQueueCache, keepAliveCache), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started")
    server.wait_for_termination()
    print("Waiting for termination")


if __name__ == '__main__':
    logging.basicConfig(format="%(threadName)s:%(message)s")
    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)
    logger.info("Main started")

    serve()
