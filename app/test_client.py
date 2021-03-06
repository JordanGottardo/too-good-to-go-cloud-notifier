import logging
import grpc
import products_pb2
import products_pb2_grpc
from datetime import datetime
import threading
import time

username="username"

def run():
    credentials = grpc.ssl_channel_credentials()
    options = [
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
        ('grpc.http2.min_time_between_pings_ms', 10000),
        ('grpc.http2.min_ping_interval_without_data_ms', 5000),
    ]

    with grpc.insecure_channel("localhost:50051") as channel:
        stub = products_pb2_grpc.ProductsManagerStub(channel)

        try:
            startMonitoringRequest = products_pb2.ProductMonitoringRequest(username=username)
            stub.StartMonitoring(startMonitoringRequest)
        except:
            pass

        print("-------------- Products --------------")

        messages = stub.GetProducts(SendKeepAlives())

        for message in messages:
            if (message.HasField("keepAlive")):
                print(f"{datetime.now()} KeepAlive received")
            else:
                product = message.productResponse
                print(f"{datetime.now()} Product available! Product ID = {product.id}\n"
                      f"Price = {product.price}\n"
                      f"Store name = {product.store.name}")


def SendKeepAlives():
    clientMessage = products_pb2.ProductClientMessage()
    clientMessage.productRequest.CopyFrom(
        products_pb2.ProductRequest(username=username))
    print(f"Getting products for user {clientMessage.productRequest.username}")

    yield clientMessage

    while True:
        print("Sleeping")
        time.sleep(10)
        clientMessage = products_pb2.ProductClientMessage()
        clientMessage.keepAlive.CopyFrom(products_pb2.KeepAlive())
        print("Returning keepAlive to send to server")
        yield clientMessage


if __name__ == "__main__":
    logging.basicConfig()
    run()
