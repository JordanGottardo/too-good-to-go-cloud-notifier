import logging
import grpc
import products_pb2
import products_pb2_grpc
from datetime import datetime

def run():
    credentials = grpc.ssl_channel_credentials()
    options = [
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
        ('grpc.http2.min_time_between_pings_ms', 10000),
        ('grpc.http2.min_ping_interval_without_data_ms', 5000),
        #('grpc.max_connection_idle_ms', 120000),
        #('grpc.max_connection_age_ms', 120000),
    ]

    #with grpc.secure_channel("too-good-to-go-cloud-notifier.jordangottardo.com:50051", credentials, options=options) as channel:
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = products_pb2_grpc.ProductsManagerStub(channel)
        print("-------------- Products --------------")
        user = products_pb2.ProductRequest(user="User1")
        print(f"Getting products for user {user.user}")

        messages = stub.GetProducts(user)

        for message in messages:
            product = message.message
            print(f"{datetime.now()} ID = {product.id}\n"
            f"Price = {product.price}")


if __name__ == "__main__":
    logging.basicConfig()
    run()
