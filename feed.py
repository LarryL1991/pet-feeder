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
restoreHeight = 2712290 # can be 0


class WalletClass():
    def __init__(self, address, viewKey, fileName, password, url):
        self.address = address
        self.viewKey = viewKey
        self.fileName = fileName
        self.password = password
        self.url = url
        self.headers = {'content-type': 'application/json'}
        self.rpc_input = ""
        self.response = ""
        self.balance = -1
        self.unlockedBalance = -1
        self.transactions = []
        self.account_index = 0
        self.subaddr_indices = [0]
        
        
    def get_balance(self):
        self.rpc_input = {
            "method": "get_balance",
            "params": {
                "in":True,
                "account_index":self.account_index, # commonly: 0
                "subaddr_indices":self.subaddr_indices # commonly: [0]
            }
        }
        self.send_request()
        
        # Need to check for failed balance response
        try:
            db = self.response.json()
            self.balance = db["result"]["balance"]
            self.unlockedBalance = db["result"]["unlocked_balance"]
            
          
        except:
            print("FAILED TO GET BALANCE! SOMETHING IS VERY VERY WRONG")
            with open("Balance.log", "w") as f:
                f.write(json.dumps(self.response.json(), indent=4))
                
    def wait_for_balance(self):
        self.refresh(restoreHeight) #CHANGE
        self.get_balance()
        while self.balance <= 0:
            print("failed to get balance, trying again")
            time.sleep(1)
            self.get_balance()
            self.get_height()
            
    def get_height(self):
        self.rpc_input = {
            "method": "get_height"
        }
        self.send_request()
        
        self.print_response()
        
    def refresh(self, start_height):
        self.rpc_input = {
            "method": "refresh",
            "params": {
                "start_height":start_height, # 0
            }
        }
        self.send_request()
        
        self.print_response()
        
    def create_wallet(self, restore_height, password):
        self.rpc_input = {
            "method": "generate_from_keys",
            "params": {
                "restore_height":restore_height, # 0
                "filename":self.fileName, # "asdfasdf"
                "address":self.address,
                "viewkey":self.viewKey,
                "password":self.password, # ""
                "autosave_current":True
            }
        }
        self.send_request()
        
        if  not self.didResponseError():
            return False
        else:
            return True
        
    def open_wallet(self):
        self.rpc_input = {
           "method": "open_wallet",
           "params": {
                "filename":self.fileName,
                "password":self.password,
                "subaddr_indices":self.subaddr_indices # [0]
            }
        }
        self.send_request()
        
        if not self.didResponseError():
            return False
        else:
            return True
        
    def didResponseError(self):
        jsonString = json.dumps(self.response.json())
        if(jsonString.find("error")>0):
            print(self.response.json()["error"]["message"])
            return False
        return True
    
    def close_wallet(self):
        self.rpc_input = {
            "method":"close_wallet"
        }
        self.send_request()
        
    def send_request(self):
        # add standard rpc values
        self.rpc_input.update({"jsonrpc": "2.0", "id": "0"})
        # execute the rpc request
        self.response = requests.post(
            self.url,
            data = json.dumps(self.rpc_input),
            headers = self.headers)
            
    def print_response(self):
        print(json.dumps(self.response.json(), indent=4))
        
    def get_transfers(self, min_height):
        self.rpc_input = {
           "method": "get_transfers",
           "params": {
                "in":True,
                "filter_by_height":True,
                "min_height":min_height,
                "pending":True,
                "pool":True,
            }
        }
        self.send_request()
        
        # TODO: Only append transactions if they are new.
        with open("transfers.log", "w") as f:
            f.write(json.dumps(self.response.json(), indent=4))
        
        db = self.response.json()
        transactions = []
        try:
            for t in db["result"]["in"]:
                transactions.append(transaction(t["amount"], t["confirmations"], t["height"], t["timestamp"], t["txid"]))
        except:
            print("failed to get transfers")
            with open("transfers.log", "w") as f:
                f.write(json.dumps(self.response.json(), indent=4))
        
        return transactions
    
    def init(self):
        
        self.close_wallet()
        # open wallet or create wallet
        #TODO: Add linux support (LOL)
        if not exists(pathToWalletFiles + "\\" + walletFileName + ".keys"):
            if not self.create_wallet(restoreHeight, walletPassword):
                print(f"Failed to create wallet {pathToWalletFiles}\{walletFileName}.keys\n")
                self.cleanup()
                return False
            print("Wallet created: " + pathToWalletFiles + "\\" + walletFileName + ".keys\n")
            return True
        
        elif self.open_wallet():
            print("Wallet opened: " + pathToWalletFiles + "\\" + walletFileName + ".keys\n")
            return True
        else:
            print(f"Failed to open wallet {pathToWalletFiles}\{walletFileName}.keys\n") 
            self.cleanup()
            return False
        
        
    def cleanup(self):
        self.close_wallet()
        print("Quitting with self.cleanup()")
    
        
def main():
    print("working")
    with open("variables.txt", "r") as f:
        pathToWalletFiles = f.readline()
        publicAddress = f.readline()
        privateViewKey = f.readline()
    print(pathToWalletFiles)
    print(publicAddress)
    print(privateViewKey)
    try:
    
        wallet = WalletClass(publicAddress, privateViewKey, walletFileName, walletPassword, monero_wallet_rpc_url)
        
        if not wallet.init():
            print("Wallet failed to initialize, quitting")
            return False
        
        
        wallet.wait_for_balance()
        wallet.print_response()
        
        wallet.close_wallet()
        
    except:
        wallet.close_wallet()

if __name__ == "__main__":
    main()
    
    
'''

class transaction():
    def __init__(self, amount, confirmations, height, timestamp, txid):
        self.amount = amount
        self.confirmations = confirmations
        self.height = height
        self.timestamp = timestamp
        self.txid = txid

def initialize(myWallet):
    myWallet.close_wallet()
    
    # open wallet or create wallet
    #TODO: Add linux support (LOL)
    if exists(pathToWalletFiles + "\\" + walletFileName + ".keys"):
        myWallet.open_wallet([0])
        print("Wallet opened: " + pathToWalletFiles + "\\" + walletFileName + ".keys\n")
    else:
        print("Wallet created: " + pathToWalletFiles + "\\" + walletFileName + ".keys\n")
        myWallet.create_wallet(restoreHeight, walletPassword)
    
    #Get balance to update wallet.
    print("Getting wallet balance now.")
    print("If this is a new wallet, the first time the balance is read could take\nup to 8 hours (from restore height 0). Please be patient.\n")
    print("If you're concerned about a hang-up, check the CPU usage of \"monero-wallet-rpc.exe\" in task manager.\n")
    state = 0
    while myWallet.balance <= 0:
        print(".", end="")
        time.sleep(10)
        myWallet.get_balance()
        myWallet.print_response()
    
    print("\n\nThe balance of the wallet is: " + str(myWallet.balance / decimals))
    print("The unlocked balance of the wallet is: " + str(myWallet.unlockedBalance / decimals))
    
def feed():
    print("performing feed operation", end="")
    # Andy put command here...
    for i in range(5):
        print(".", end="")
        time.sleep(1)
        
    print("")
    
def print_UI(myWallet, handledTransactions, amountGained, amountSpent, state):
    system("cls")
    print(f"Wallet Balance: {myWallet.balance/decimals} Unlocked Balance: {myWallet.unlockedBalance/decimals}")
    print("")
    print(f"XMR Gained: {amountGained} XMR - XMR Used for feeding: {amountSpent} XMR - XMR remaining for future transactions: {amountGained - amountSpent} XMR")
    print("")
    print(f"Current price of monero is: ${monero_price}")
    print("")
    print("Completed transactions:")
    for t in handledTransactions[-10:]:
        print(f"TXID: {t.txid} Amount: {t.amount/decimals} XMR")
        
    print("."*state)
        
def getUSDValue(amount):
    return amount * monero_price #obviously use binance API to get the price....

def getXMRValue(amount):
    return amount / monero_price
        
def main():
    #Run monero-wallet-rpc in background here.
    
    #maybe a delay??
    
    # set up wallet with user provided specs
    myWallet = wallet(publicAddress, privateViewKey, walletFileName, walletPassword, monero_wallet_rpc_url)
    initialize(myWallet)
    
    transactions = myWallet.get_transfers(check_for_transfers_after_height)
    
    print(f"\nTransactions that exist at run time from block height of {check_for_transfers_after_height}:")
    for t in transactions:
            print(f"TXID = {t.txid} amount = {t.amount/decimals} XMR")
    
    print("\n\nWaiting 3 seconds before clearing the CLI")
    # myWallet.close_wallet()
    time.sleep(3)
    system("cls")
    print("Checking for new transactions...")
    
    handledTransactions = []
    unhandledTransactions = []
    state = 0
    amountGained = 0
    amountSpent = 0
    
    # Main Loop
    while True:
        # myWallet.open_wallet([0]) #open wallet every loop to test something
        myWallet.get_balance()
        while myWallet.balance <= 0:
            print(":", end="")
            time.sleep(10)
            myWallet.get_balance()
            myWallet.print_response()
        newTransactions = myWallet.get_transfers(check_for_transfers_after_height)
        
        state += 1
        if state > 3:
            state = 0
        print_UI(myWallet, handledTransactions, amountGained, amountSpent, state)
        
            
        for nT in newTransactions:
            transaction_is_in_list = False
            for t in transactions:
                if t.txid == nT.txid:
                    transaction_is_in_list = True
            if transaction_is_in_list == False:
                transactions.append(nT)
                unhandledTransactions.append(nT)
        
        while unhandledTransactions != []:
            newTransaction = unhandledTransactions.pop()
            print(f"Receieved new transaction txid: {newTransaction.txid} amount: {newTransaction.amount/decimals} XMR")
            handledTransactions.append(newTransaction)
            amountGained += newTransaction.amount/decimals
            USD_Value = getUSDValue(amountGained - amountSpent)
            if USD_Value >= payment_per_feed:
                feed()
                spend = getXMRValue(payment_per_feed)
                # amountGained = amountGained - spend
                amountSpent += spend
        
        # myWallet.close_wallet() #close wallet every loop to test something
        time.sleep(10)
    #and close the wallet once the code has finished (it won't ever finish though)
'''