# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import products_pb2 as products__pb2


class ProductsManagerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.StartMonitoring = channel.unary_unary(
                '/ProductsManager/StartMonitoring',
                request_serializer=products__pb2.ProductMonitoringRequest.SerializeToString,
                response_deserializer=products__pb2.Empty.FromString,
                )
        self.StopMonitoring = channel.unary_unary(
                '/ProductsManager/StopMonitoring',
                request_serializer=products__pb2.ProductStopMonitoringRequest.SerializeToString,
                response_deserializer=products__pb2.Empty.FromString,
                )
        self.GetProducts = channel.stream_stream(
                '/ProductsManager/GetProducts',
                request_serializer=products__pb2.ProductClientMessage.SerializeToString,
                response_deserializer=products__pb2.ProductServerMessage.FromString,
                )


class ProductsManagerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def StartMonitoring(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StopMonitoring(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetProducts(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ProductsManagerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'StartMonitoring': grpc.unary_unary_rpc_method_handler(
                    servicer.StartMonitoring,
                    request_deserializer=products__pb2.ProductMonitoringRequest.FromString,
                    response_serializer=products__pb2.Empty.SerializeToString,
            ),
            'StopMonitoring': grpc.unary_unary_rpc_method_handler(
                    servicer.StopMonitoring,
                    request_deserializer=products__pb2.ProductStopMonitoringRequest.FromString,
                    response_serializer=products__pb2.Empty.SerializeToString,
            ),
            'GetProducts': grpc.stream_stream_rpc_method_handler(
                    servicer.GetProducts,
                    request_deserializer=products__pb2.ProductClientMessage.FromString,
                    response_serializer=products__pb2.ProductServerMessage.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'ProductsManager', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ProductsManager(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def StartMonitoring(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ProductsManager/StartMonitoring',
            products__pb2.ProductMonitoringRequest.SerializeToString,
            products__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StopMonitoring(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ProductsManager/StopMonitoring',
            products__pb2.ProductStopMonitoringRequest.SerializeToString,
            products__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetProducts(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/ProductsManager/GetProducts',
            products__pb2.ProductClientMessage.SerializeToString,
            products__pb2.ProductServerMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
