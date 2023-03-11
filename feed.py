import requests
import json
import time
from os.path import exists
from os import system

monero_wallet_rpc_url = "http://127.0.0.1:18082/json_rpc"
pathToWalletFiles = ""

publicAddress = ""
privateViewKey = ""
walletFileName = "wallet-with-view-key"
walletPassword = ""


class WalletClass():
    def __init__(self, address, viewKey, fileName, password, url, filePath, restoreHeight):
        self.address = address
        self.viewKey = viewKey
        self.fileName = fileName
        self.password = password
        self.url = url
        self.filePath = filePath
        self.restoreHeight = restoreHeight
        self.headers = {'content-type': 'application/json'}
        self.rpc_input = ""
        self.response = ""
        self.balance = -1
        self.unlockedBalance = -1
        self.transfers = []
        self.oldTransfers = []
        self.account_index = 0
        self.subaddr_indices = [0]
        self.height = restoreHeight
        self.excessXMR = 0
        self.minimumFee = 10000

    def get_balance(self):
        self.rpc_input = {
            "method": "get_balance",
            "params": {
                "in": True,
                "account_index": self.account_index,  # commonly: 0
                "subaddr_indices": self.subaddr_indices  # commonly: [0]
            }
        }
        self.send_request()

        # Need to check for failed balance response
        if self.responseSuccess():
            db = self.response.json()
            self.balance = db["result"]["balance"]
            self.unlockedBalance = db["result"]["unlocked_balance"]
            return self.balance
        else:
            print("FAILED TO GET BALANCE! SOMETHING IS VERY VERY WRONG")
            with open("Balance.log", "w") as f:
                f.write(json.dumps(self.response.json(), indent=4))
            return -1

    def get_height(self):
        self.rpc_input = {
            "method": "get_height"
        }
        self.send_request()
        if self.responseSuccess():
            db = self.response.json()
            self.height = db["result"]["height"]
            return self.height
        else:
            print("FAILED TO GET HEIGHT!")
            with open("height.log", "w") as f:
                f.write(json.dumps(self.response.json(), indent=4))
            return -1

    def refresh(self, start_height):
        self.rpc_input = {
            "method": "refresh",
            "params": {
                "start_height": start_height,  # 0
            }
        }
        self.send_request()
        return self.responseSuccess()

    def create_wallet(self, restore_height, password):
        self.rpc_input = {
            "method": "generate_from_keys",
            "params": {
                "restore_height": restore_height,  # 0
                "filename": self.fileName,  # "asdfasdf"
                "address": self.address,
                "viewkey": self.viewKey,
                "password": self.password,  # ""
                "autosave_current": True
            }
        }
        self.send_request()
        return self.responseSuccess()

    def open_wallet(self):
        self.rpc_input = {
            "method": "open_wallet",
            "params": {
                "filename": self.fileName,
                "password": self.password,
                "subaddr_indices": self.subaddr_indices  # [0]
            }
        }
        self.send_request()

        return self.responseSuccess()

    def responseSuccess(self):
        jsonString = json.dumps(self.response.json())
        if (jsonString.find("error") > 0):
            print(self.response.json()["error"]["message"])
            return False
        return True

    def close_wallet(self):
        # self.save_wallet() # RE ENABLE SAVING AS SOON AS TESTING IS DONE
        self.rpc_input = {
            "method": "close_wallet"
        }
        self.send_request()

    def save_wallet(self):
        self.rpc_input = {
            "method": "store"
        }
        self.send_request()

    def send_request(self):
        # add standard rpc values
        self.rpc_input.update({"jsonrpc": "2.0", "id": "0"})
        # execute the rpc request
        self.response = requests.post(
            self.url,
            data=json.dumps(self.rpc_input),
            headers=self.headers)

    def print_response(self):
        print(json.dumps(self.response.json(), indent=4))

    def clear_transfers(self):
        self.transfers = []

    def get_transfers(self, min_height, max_height):
        self.rpc_input = {
            "method": "get_transfers",
            "params": {
                "in": True,
                "filter_by_height": True,
                "min_height": min_height,
                # Using max height for now for testing purposes only.
                "max_height": max_height,
                "pending": True,
                "pool": True,
            }
        }
        self.send_request()

        db = self.response.json()
        if self.responseSuccess():
            with open("transfers.log", "w") as f:
                f.write(json.dumps(self.response.json(), indent=4))

            if len(db["result"]) == 0:
                self.transfers = []
                return self.transfers

            # When reading from the mempool this will be ["result"]["pool"] I need to find a way to handle that.
            for t in db["result"]["in"]:
                temp_dict = {"amount": t["amount"], "confirmations": t["confirmations"],
                             "height": t["height"], "timestamp": t["timestamp"], "txid": t["txid"]}
                if not temp_dict in self.transfers:
                    self.transfers.append(temp_dict)

        else:
            print("failed to get transfers")
            with open("transfers.log", "w") as f:
                f.write(json.dumps(self.response.json(), indent=4))

        return self.transfers

    def auto_refresh(self, enable):
        self.rpc_input = {
            "method": "auto_refresh",
            "params": {
                "enable": enable
            }
        }
        self.send_request()

    def init(self):

        self.close_wallet()
        # open wallet or create wallet
        # TODO: Add linux support (LOL)
        if not exists(f"{self.filePath}\\{walletFileName}.keys"):
            if not self.create_wallet(self.restoreHeight, self.password):
                print(
                    f"Failed to create wallet {self.filePath}\{walletFileName}.keys\n")
                self.cleanup()
                return False
            print(
                f"Wallet created: {self.filePath}\\{walletFileName}.keys\n")
            return True

        elif self.open_wallet():
            print(f"Wallet opened: {self.filePath}\\{walletFileName}.keys\n")
            return True
        else:
            print(
                f"Failed to open wallet {self.filePath}\{walletFileName}.keys\n")
            self.cleanup()
            return False

    def cleanup(self):
        self.close_wallet()

    def update(self):
        # Just a template for what I think will happen in update(). I will need to handle this on a transaction by transaction basis.

        # should just check from current height (testing) self.height
        self.get_transfers(2838688, 4839394)
        if len(self.transfers) > 0:
            print("received new transfer:")
            print(self.transfers)
            for transfer in self.transfers:
                self.oldTransfers.append(transfer)
                if transfer["amount"] > 10000000:
                    print(f"{transfer['amount']} > 10000000")
                    self.excessXMR += transfer["amount"] - self.minimumFee
                    print(f"excessXMR = {self.excessXMR}")
                else:
                    print(f"{transfer['amount']} < 10000000")
                    self.excessXMR += transfer["amount"]
            self.clear_transfers()


def main():
    print("working")
    with open("variables.txt", "r") as f:
        pathToWalletFiles = f.readline().strip()
        publicAddress = f.readline().strip()
        privateViewKey = f.readline().strip()
    restoreHeight = 2712290  # can be 0
    try:
        wallet = WalletClass(publicAddress, privateViewKey, walletFileName,
                             walletPassword, monero_wallet_rpc_url, pathToWalletFiles, restoreHeight)

        if not wallet.init():
            print("Wallet failed to initialize, quitting")
            return False
        wallet.auto_refresh(False)

        wallet.get_height()
        print(
            f"Refreshing wallet from block height: {wallet.height}. This could take a very long time if this is the first time this wallet has been opened.")
        wallet.refresh(restoreHeight)  # refresh the wallet manually
        wallet.get_height()  # get the new height

        wallet.get_balance()

        print(f"The wallet contains {wallet.balance/(10**12)} XMR")

        wallet.get_transfers(restoreHeight, 2838688)

        print(
            f"Transfers from {restoreHeight} to {wallet.height}({wallet.height-restoreHeight} blocks):")
        print(wallet.transfers)

        print("\n\nClearing old transfers...")
        wallet.clear_transfers()

        print("Waiting for transfers")
        loop = True
        while loop:
            wallet.update()

            # if statement here to decide what to do after wallet update maybe.

            time.sleep(10)
            wallet.refresh(wallet.height)

        wallet.close_wallet()  # save and close the wallet SAVE CURRENTLY DISABLED FOR TESTING

    except Exception as e:
        print(e.args)
        wallet.close_wallet()


if __name__ == "__main__":
    main()
