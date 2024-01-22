import time
import random
import csv
from web3 import Web3
from datetime import datetime

import sys
sys.path.insert(1,'PATH_TO_YOU_ROOT_DIRECTORY/helpers')
import helper as hlp 

w3 = Web3(Web3.HTTPProvider(hlp.NODE_URL))

SENDER_PRIVATE_KEY = ''
SENDER_ADDRESS = w3.to_checksum_address('')
RECEIVER_ADDRESS = w3.to_checksum_address('')
AMOUNT_TO_SEND = 101000000000000000000  

contract = w3.eth.contract(address=hlp.TokenA_CONTRACT_ADDRESS, abi=hlp.TokenA_CONTRACT_ABI)

def send_token_transaction():
    try:
        nonce = w3.eth.get_transaction_count(SENDER_ADDRESS)
        txn = contract.functions.transfer(RECEIVER_ADDRESS, AMOUNT_TO_SEND).build_transaction({
            'chainId': 97,
            'gas': 2000000,
            'gasPrice': 20 * 10**9,  # 20 gwei in wei
            'nonce': nonce,
        })
        signed_txn = w3.eth.account.sign_transaction(txn, SENDER_PRIVATE_KEY)
        txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f'Transaction Hash: {txn_hash.hex()}')

        # Wait for a few block confirmations (e.g., 1-2 minutes for Ethereum, 10-20 seconds for BSC)
        time.sleep(30)  # Adjust this value based on your network

        # Check the transaction receipt
        receipt = w3.eth.get_transaction_receipt(txn_hash)

        if receipt and receipt.status == 1:
            # Transaction was successful, log hash to transaction_hashes.csv
            with open("transaction_hashes.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([txn_hash.hex()])
        else:
            # Transaction failed, log hash to exceptions.csv
            with open("exceptions.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([f"Transaction {txn_hash.hex()} failed"])

    except Exception as e:
        print(e)


if __name__ == "__main__":
    for _ in range(1):
        send_token_transaction()
        sleep_duration = random.randint(1, 20)
        print(f"Sleeping for {sleep_duration} seconds...")
        time.sleep(sleep_duration)
