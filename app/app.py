from tgtg import TgtgClient
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--email', type=str, help='TooGoodToGo Email')
parser.add_argument('--password', type=str, help='TooGoodToGo password')
args = parser.parse_args()

email = args.email
password = args.password

client = TgtgClient(email=email, password=password)
items = client.get_items()
print(items)
