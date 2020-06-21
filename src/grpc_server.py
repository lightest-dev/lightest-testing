from protos.CodeTester_pb2 import *
from protos.CodeTester_pb2_grpc import CodeTesterServicer

class GrpcServer(CodeTesterServicer):
    def CompileChecker(self, request: CheckerRequest, context):
        return CheckerResponse()
