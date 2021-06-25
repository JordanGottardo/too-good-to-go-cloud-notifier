from concurrent import futures
import logging
import argparse
from too_good_to_go_client import TooGoodToGoClient
from products_queue import ProductsQueue
import grpc
import products_pb2
import products_pb2_grpc
from event import Event


class ProductsServicer(products_pb2_grpc.ProductsManagerServicer):

    def __init__(self, email, password):
        self.__InitLogging()

        self.logger.info("ProductsServicer constructor")

        client = TooGoodToGoClient(email, password)
        client.StartMonitor()
        self.productsQueue = ProductsQueue(client)

    def GetProducts(self, request, context):
        self.logger.info(f"Received request for user {request.user}")
        for item in self.productsQueue:
            self.logger.debug(f"Gotten {item} from queue")
            yield item

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
    products_pb2_grpc.add_ProductsManagerServicer_to_server(
        ProductsServicer(email, password), server)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', type=str, help='TooGoodToGo Email')
    parser.add_argument('--password', type=str, help='TooGoodToGo password')
    args = parser.parse_args()

    email = args.email
    password = args.password

    serve()
