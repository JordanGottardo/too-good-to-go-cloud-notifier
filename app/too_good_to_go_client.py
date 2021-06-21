from tgtg import TgtgClient


class TooGoodToGoClient:

    def __init__(self, email, password):
        print(
            f"TooGoodToGoClient Constructor: initializing for user {email} with password {password}")
        self.email = email
        self.password = password
        self.client = TgtgClient(email=email, password=password)

    def GetProducts(self):
        return self.client.get_items()