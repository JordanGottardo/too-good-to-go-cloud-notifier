from concurrent import futures
import logging
import argparse
from too_good_to_go_client import TooGoodToGoClient
import grpc
import products_pb2
import products_pb2_grpc


class ProductsServicer(products_pb2_grpc.ProductsManagerServicer):

    def __init__(self, email, password):
        print("Constructor")
        self.client = TooGoodToGoClient(email, password)

    def GetProducts(self, request, context):
        print(f"Received request for user {request.user}")
        for item in self.client.GetProducts():
            item["item"]["item_id"]
            yield products_pb2.ProductResponse(id=item["item"]["item_id"])


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
    print("Main started")
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', type=str, help='TooGoodToGo Email')
    parser.add_argument('--password', type=str, help='TooGoodToGo password')
    args = parser.parse_args()

    email = args.email
    password = args.password
    
    logging.basicConfig()
    serve()

