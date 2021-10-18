from concurrent import futures
from datetime import datetime
import logging
from keep_alive_cache import ShortLivedKeepAliveCache, LongLivedKeepAliveCache
from products_queue_cache import ProductsQueueCache
from too_good_to_go_client import TooGoodToGoClient
from tgtg import TgtgLoginError, TgtgAPIError
from products_queue import ProductsQueue
import grpc
from products_pb2_grpc import ProductsManagerServicer, add_ProductsManagerServicer_to_server
from products_pb2 import Empty, ProductMonitoringRequest, ProductStopMonitoringRequest
from threading import RLock, Thread


class ProductsServicer(ProductsManagerServicer):

    def __init__(
            self,
            productsQueueCache: ProductsQueueCache,
            shortLivedKeepAliveCache: ShortLivedKeepAliveCache,
            longLivedKeepAliveCache: LongLivedKeepAliveCache):
        self.__InitLogging()
        self.logger.info("ProductsServicer constructor")
        self.productsQueueCache = productsQueueCache
        self.shortLivedKeepAliveCache = shortLivedKeepAliveCache
        self.longLivedKeepAliveCache = longLivedKeepAliveCache
        self.subscriptionLock = RLock()

    def StartMonitoring(self, request: ProductMonitoringRequest, context):
        with self.subscriptionLock:
            self.logger.info(
                f"ProductsServicer: Received StartMonitoring request for user {request.username}")
            username = request.username

            if (self.productsQueueCache.Contains(username)):
                self.logger.error(
                    f"ProductsServicer: Subscription for user {username} already exists. Either use the GetProducts RPC or Stop then Start subscription")
                context.abort(grpc.StatusCode.ALREADY_EXISTS,
                              f"Subscription for user {username} already exists")

            client = TooGoodToGoClient(username, request.password)
            self.__FailIfCannotAccessTgTgApi(client, context, username)

            productsQueue = ProductsQueue(client)
            productsQueue.StartMonitoring()
            self.productsQueueCache.Add(username, productsQueue)
            self.longLivedKeepAliveCache.AddOrUpdate(username, datetime.now())

            self.logger.info(
                f"ProductsServicer: Returning from StartMonitoring RPC")
            return Empty()

    def StopMonitoring(self, request: ProductStopMonitoringRequest, context):
        with self.subscriptionLock:
            self.logger.info(
                f"ProductsServicer: Received StopMonitoring request for user {request.username}")
            username = request.username

            self.productsQueueCache.HardStopMonitoring(username)

            self.logger.info(
                f"ProductsServicer: Returning from StopMonitoring RPC")

            return Empty()

    def GetProducts(self, requestIterator, context):
        productRequest = next(requestIterator).productRequest
        username = productRequest.username

        self.logger.info(
            f"ProductsServicer: Received GetProducts request for user {username}")

        if (not self.productsQueueCache.Contains(username)):
            self.logger.error(
                f"ProductsServicer: Monitoring has not yet started for user {username}. Invoke StartMonitoring RPC before this one")
            context.abort(grpc.StatusCode.FAILED_PRECONDITION,
                          "Monitoring has not yet started. Invoke StartMonitoring RPC before this one")

        self.__AddChannelClosedCallback(context, username)

        self.__StartReceivingKeepAlivesAsync(requestIterator, username)
        self.productsQueueCache.RestartMonitoring(username)

        for item in self.productsQueueCache.Get(username):
            if (item.HasField("keepAlive")):
                self.logger.debug(
                    f"ProductsServicer: Sending KeepAlive, user {username}")
            else:
                self.logger.debug(
                    f"Gotten {item.productResponse.id} {item.productResponse.store.name} Price={item.productResponse.price} decimals={item.productResponse.decimals} from queue. Returning it to the client. User {username}")
            yield item

        self.logger.debug(
            f"ProductsServicer: Channel closed for user {username}. Returning from GetProducts RPC")

    def __AddChannelClosedCallback(self, context, username):
        def __GrpcChannelClosedCallback():
            self.logger.debug(
                f"ProductsServicer: GRPC channel has been closed from client, User {username}")
            self.productsQueueCache.SoftStopMonitoring(username)

        context.add_callback(__GrpcChannelClosedCallback)

    def __StartReceivingKeepAlivesAsync(self, requestIterator, identifier):
        self.__UpdatedKeepAliveCache(identifier)
        thread = Thread(
            target=self.__StartReceivingKeepAlives, args=(requestIterator, identifier))
        thread.daemon = True
        thread.start()

    def __StartReceivingKeepAlives(self, requestIterator, identifier):
        try:
            for request in requestIterator:
                if (request.HasField("keepAlive")):
                    self.logger.debug(
                        f"ProductsServicer:: Received KeepAlive from client {identifier}")
                    self.__UpdatedKeepAliveCache(identifier)
                else:
                    self.logger.debug(
                        f"ProductsServicer: Unknown request received from client {identifier}")
        except Exception as e:
            self.logger.debug(
                f"ProductsServicer: Error while reading keepAlives from client. Error: {e}")

    def __UpdatedKeepAliveCache(self, identifier):
        self.shortLivedKeepAliveCache.AddOrUpdate(identifier, datetime.now())
        self.longLivedKeepAliveCache.AddOrUpdate(identifier, datetime.now())

    def __FailIfCannotAccessTgTgApi(self, client, context, username):
        try:
            client.TestCredentials()
        except TgtgLoginError:
            self.logger.error(
                f"ProductsServicer: Invalid credentials for user {username}")
            context.abort(grpc.StatusCode.UNAUTHENTICATED,
                          f"Invalid credentials for user {username}")
        except TgtgAPIError:
            self.logger.error(
                f"ProductsServicer: Error while accessing TgTg API for user {username}")
            context.abort(grpc.StatusCode.INTERNAL,
                          f"Could not access TgTg API {username}")

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
    shortLivedKeepAliveCache = ShortLivedKeepAliveCache(productsQueueCache)
    longLivedKeepAliveCache = LongLivedKeepAliveCache(productsQueueCache)
    productsServicer = ProductsServicer(
        productsQueueCache,
        shortLivedKeepAliveCache,
        longLivedKeepAliveCache)

    add_ProductsManagerServicer_to_server(productsServicer, server)
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
