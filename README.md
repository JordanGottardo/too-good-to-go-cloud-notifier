# too-good-to-go-cloud-notifier

**TooGoodToGo Cloud Notifier** is a dockerized server side component which notifies you when your favourite products become available on [TooGoodToGo](https://toogoodtogo.com/en-us).

If you're looking for the client mobile application, visit https://github.com/JordanGottardo/too-good-to-go-notifier-mobile-app.

This component, written in Python, uses [gRPC](https://grpc.io/) to notify when a product is available. Communication with TooGoodToGo API is carried out through the [tgtg-python](https://github.com/ahivert/tgtg-python/) client.

Disclaimer: TooGoodToGo Cloud Notifier requires TooGoodToGo username and password (i.e., the same credentials you use to log into the TooGoodToGo mobile app) in order to access your favourite products. These credentials are only used to access the APIs and are not stored in any way.

# Test locally
You can test it out locally by building the docker image and running the container with the following commands:
```
docker build -t too-good-to-go-cloud-notifier .
docker run -p 50051:50051 too-good-to-go-cloud-notifier
```

Now the server is reachable through _localhost:50051_.

A sample gRPC Python client is included in the _app/test_client.py_ file. You can use it for testing purposes by inserting your credentials into the code.

You can launch the test client by creating a Pyhon virtual environment and installing requirements using the following commands (requires Python 3.9):
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python .\app\test_client.py
```

Below an example of notification when a product is available.
![Product notification](https://imgur.com/a/LAZBq7z)

Notice that  [gRPC bidirectional streaming](https://grpc.io/docs/what-is-grpc/core-concepts/#bidirectional-streaming-rpc) has been implemented to retrieve products. Hence, client to server keep alives are required to keep the connection open.

# API
APIs are defined in the _app/protos/products.proto_ file.
## StartMonitoring
Requires TooGoodToGo username and password. When invoked with valid credentials, starts monitoring products for such user, polling the TooGoodToGo server.
## GetProducts 
Must be invoked after _StartMonitoring_. Requires a TooGoodToGo username. Returns a bidirectional stream into which products related to the specified user are inserted when they become available on TooGoodToGo. Keep alives are sent periodically from server to client. Moreover, to keep the connection open, client to server keep alives must be sent.
## StopMonitoring
Requires TooGoodToGo username. Stops monitoring products for the specified user.
