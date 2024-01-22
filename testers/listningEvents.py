from web3 import Web3, HTTPProvider
import sys
sys.path.insert(1,'PATH_TO_YOU_ROOT_DIRECTORY/helpers')
import helper as hlp 


# BUSD_address = ''
# BUSD_abi = ''


w3 = Web3(HTTPProvider(hlp.NODE_URL))
contract = w3.eth.contract(address=hlp.USDT_CONTRACT_ADDRESS, abi=hlp.USDT_CONTRACT_ABI)
transfer_event_filter = contract.events.Transfer.create_filter(fromBlock= 34316215, toBlock = 34316225)
# print(transfer_event_filter.get_all_entries())
# print(len(transfer_event_filter.get_all_entries()))

events = transfer_event_filter.get_new_entries()

print(events)
print(len(events))

for event in events:
    print(event)
    print("--------")
