from concurrent import futures
import logging
from too_good_to_go_client import TooGoodToGoClient
from products_queue import ProductsQueue
import grpc
from products_pb2_grpc import ProductsManagerServicer, add_ProductsManagerServicer_to_server
from products_pb2 import ProductRequest
import random


class ProductsServicer(ProductsManagerServicer):

    def __init__(self):
        self.__InitLogging()

        self.logger.info("ProductsServicer constructor")

    def GetProducts(self, request: ProductRequest, context):
        identifier = random.randint(0, 99999999999999999999999999999999)
        self.logger.info(f"Received request for user {request.username}, ID {identifier}")

        context.add_callback(self.__GrpcChannelClosedCallback)

        client = TooGoodToGoClient(request.username, request.password)
        client.StartMonitor()
        self.productsQueue = ProductsQueue(client)
        for item in self.productsQueue:
            if (item is None):
                self.logger.debug(
                    f"Monitoring ended for user {request.username}, ID {identifier}")
                return

            if (item.HasField("keepAlive")):
                self.logger.debug(f"Sending KeepAlive, ID {identifier}")
            else:
                self.logger.debug(
                    f"Gotten {item.productResponse.id} {item.productResponse.store.name} from queue. Returning it to the client. ID {identifier}")
            yield item

    def __GrpcChannelClosedCallback(self):
        self.logger.debug("GRPC channel has been closed, ID {identifier}")
        self.productsQueue.StopMonitoring()

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
    add_ProductsManagerServicer_to_server(ProductsServicer(), server)
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
