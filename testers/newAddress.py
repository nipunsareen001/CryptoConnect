from web3 import Web3, Account
import os

# Generate a new private key
private_key = Web3.to_hex(os.urandom(32))
print(f"Private Key: {private_key}")

# Get the public address
account = Account.from_key(private_key)
print(f"Address: {account.address}")
