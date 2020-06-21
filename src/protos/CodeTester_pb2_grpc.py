# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import protos.CodeTester_pb2 as CodeTester__pb2


class CodeTesterStub(object):
    """Missing associated documentation comment in .proto file"""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CompileChecker = channel.unary_unary(
                '/CodeTester/CompileChecker',
                request_serializer=CodeTester__pb2.CheckerRequest.SerializeToString,
                response_deserializer=CodeTester__pb2.CheckerResponse.FromString,
                )
        self.TestUpload = channel.unary_unary(
                '/CodeTester/TestUpload',
                request_serializer=CodeTester__pb2.TestingRequest.SerializeToString,
                response_deserializer=CodeTester__pb2.TestingResponse.FromString,
                )
        self.GetStatus = channel.unary_unary(
                '/CodeTester/GetStatus',
                request_serializer=CodeTester__pb2.CheckerStatusRequest.SerializeToString,
                response_deserializer=CodeTester__pb2.CheckerStatusResponse.FromString,
                )


class CodeTesterServicer(object):
    """Missing associated documentation comment in .proto file"""

    def CompileChecker(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TestUpload(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetStatus(self, request, context):
        """Missing associated documentation comment in .proto file"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_CodeTesterServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CompileChecker': grpc.unary_unary_rpc_method_handler(
                    servicer.CompileChecker,
                    request_deserializer=CodeTester__pb2.CheckerRequest.FromString,
                    response_serializer=CodeTester__pb2.CheckerResponse.SerializeToString,
            ),
            'TestUpload': grpc.unary_unary_rpc_method_handler(
                    servicer.TestUpload,
                    request_deserializer=CodeTester__pb2.TestingRequest.FromString,
                    response_serializer=CodeTester__pb2.TestingResponse.SerializeToString,
            ),
            'GetStatus': grpc.unary_unary_rpc_method_handler(
                    servicer.GetStatus,
                    request_deserializer=CodeTester__pb2.CheckerStatusRequest.FromString,
                    response_serializer=CodeTester__pb2.CheckerStatusResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'CodeTester', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class CodeTester(object):
    """Missing associated documentation comment in .proto file"""

    @staticmethod
    def CompileChecker(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/CodeTester/CompileChecker',
            CodeTester__pb2.CheckerRequest.SerializeToString,
            CodeTester__pb2.CheckerResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def TestUpload(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/CodeTester/TestUpload',
            CodeTester__pb2.TestingRequest.SerializeToString,
            CodeTester__pb2.TestingResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetStatus(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/CodeTester/GetStatus',
            CodeTester__pb2.CheckerStatusRequest.SerializeToString,
            CodeTester__pb2.CheckerStatusResponse.FromString,
            options, channel_credentials,
            call_credentials, compression, wait_for_ready, timeout, metadata)
