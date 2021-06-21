from concurrent import futures
import logging
import argparse
from too_good_to_go_client import TooGoodToGoClient
from products_queue import ProductsQueue
import grpc
import products_pb2
import products_pb2_grpc
import threading


class ProductsServicer(products_pb2_grpc.ProductsManagerServicer):

    def __init__(self, email, password):
        logging.basicConfig(format="%(threadName)s:%(message)s")
        self.logger = logging.getLogger("ProductsQueue")
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("ProductsQueue constructor")
        self.logger.info("Constructor")
        self.client = TooGoodToGoClient(email, password)
        self.productsQueue = ProductsQueue()

    def GetProducts(self, request, context):
        self.logger.info(f"Received request for user {request.user}")
        print(threading.get_ident())

        self.productsQueue.startAdd()

        for item in self.productsQueue:
            self.logger.debug(f"Gotten {item}")
            yield item
        # for item in self.client.GetProducts():
            # print(f"Retrieved {item['item']['item_id']}")
            # yield self.productsQueue.get()
            # yield products_pb2.ProductResponse(id=item["item"]["item_id"])


def serve():
    print("Serve")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
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
