import logging
import grpc
import products_pb2
import products_pb2_grpc


def run():
    credentials = grpc.ssl_channel_credentials()
    with grpc.secure_channel("too-good-to-go-cloud-notifier.jordangottardo.com:50051", credentials) as channel:
        stub = products_pb2_grpc.ProductsManagerStub(channel)
        print("-------------- Products --------------")
        user = products_pb2.ProductRequest(user="User1")
        print(f"Getting products for user {user.user}")

        products = stub.GetProducts(user)

        for product in products:
            print(product.id)


if __name__ == "__main__":
    logging.basicConfig()
    run()
