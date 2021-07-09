$ProductsGrpcFilePath = "..\app\products_pb2_grpc.py"
$ProductsFilePath = "..\app\products_pb2.py"

if (Test-Path $ProductsGrpcFilePath) {
    Remove-Item $ProductsGrpcFilePath
}

if (Test-Path $ProductsFilePath) {
    Remove-Item $ProductsFilePath
}

# python -m grpc_tools.protoc -I../app/protos --python_out=../app --grpc_python_out=../app ../app/protos/products.proto