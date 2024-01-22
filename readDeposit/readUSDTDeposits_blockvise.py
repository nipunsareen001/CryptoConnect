import csv
from datetime import datetime
from web3 import Web3, HTTPProvider
import time 
from decimal import Decimal

import sys
sys.path.insert(1,'PATH_TO_YOU_ROOT_DIRECTORY/helpers')
import helper as hlp 


print("------------RUNNING--------------")

# Global set to store addresses
addresses_set = set()

# Global variable for tracking the last reload time
last_reload_time = 0

def fetchCurrentBlockNumber():
    w3 = Web3(HTTPProvider(hlp.NODE_URL))
    return w3.eth.block_number

def fetchCurrentBlockNumber2(w3):
    return w3.eth.block_number

def setLastCheckBlockNumber(blockNumber):
    cursor, conn = hlp.getDatabase()
    cursor.execute('UPDATE LastCheckedUsdtBlock SET last_block_number = ? WHERE deposit_type = ? ', (blockNumber, hlp.TokenName.USDT.value))
    conn.commit()
    hlp.closeDatabase(conn)


def lastCheckBlockNumber():
    cursor, conn = hlp.getDatabase()
    cursor.execute('SELECT last_block_number FROM LastCheckedUsdtBlock WHERE deposit_type = ? ', (hlp.TokenName.USDT.value))
    response = cursor.fetchall()
    hlp.closeDatabase(conn)

    return response[0][0]

def sendExceptionMail(exceptionData):
    subject = 'AUTO-DEPOSIT | USDT HAS FACED AN EXCEPTION!'
    text_message = (
        "AUTO-DEPOSIT | USDT HAS FACED AN EXCEPTION!.\r\n"
        "EXception data: .\r\n"
        +str(exceptionData[0])+str(exceptionData[1])+str(exceptionData[2])+".\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)

def updateExceptionLogs(exceptionData):
    with open("./depositUSDTExceptionLogs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(exceptionData)

def handleExpection(exceptionData):
    updateExceptionLogs(exceptionData)
    sendExceptionMail(exceptionData)

def updateLogs(logData):
    with open("./depositUSDTLogs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(logData)


def load_addresses_into_set():
    """Load addresses from the database into the in-memory set."""
    global addresses_set

    # Clear the existing data in the set
    addresses_set.clear()

    # Load new addresses from the database
    cursor, conn = hlp.getDatabase()
    cursor.execute('SELECT nvc_address FROM member_deposit_address')
    addresses = cursor.fetchall()
    hlp.closeDatabase(conn)

    # Add the new addresses to the set
    for address in addresses:
        addresses_set.add(address[0])


def address_exists(address):
    """Check if the given address exists in the addresses set."""
    return address in addresses_set


def handle_event(event):
    try:
        to_address = event['args']['to']
        if address_exists(to_address):
            value_trx = (event['args']['value'])
            value_trx_str = str(value_trx)
            decimal_value_trx_str = Decimal(value_trx_str)
            value_token = decimal_value_trx_str / Decimal('1e18')

            cursor, conn = hlp.getDatabase()
            cursor.execute("EXEC InsertUniqueBlockchainDepositLogWithCheck ?, ?, ?, ?, ?, ?, ?",
                (event['transactionHash'].hex(), event['args']['from'], event['args']['to'], value_token, value_trx_str, hlp.TokenName.USDT.value, datetime.utcnow()))

            result_set = cursor.fetchone() 
            recordAdded = result_set[0]
            conn.commit()
            hlp.closeDatabase(conn)

            if recordAdded:
                updateLogs(['SUCCESS: ', str(event['transactionHash'].hex()), str(event['args']['from']), str(value_token), str((event['args']['value'])), str(datetime.utcnow())])

    except Exception as e:
        handleExpection(['handle_event()', str(e), str(datetime.utcnow())])



def main():

    load_addresses_into_set()
    setLastCheckBlockNumber(fetchCurrentBlockNumber() - 10)

    global last_reload_time
    last_reload_time = time.time()  # Set the last reload time to current time

    while True:

        if time.time() - last_reload_time >= 3600:  # 3600 seconds in an hour
            load_addresses_into_set()
            last_reload_time = time.time()  # Reset the last reload time

        try: 
            w3 = Web3(HTTPProvider(hlp.NODE_URL))
            fromBlockNumber = lastCheckBlockNumber() + 1
            toBlockNumber = fromBlockNumber + 5
            currentBlockNumber = fetchCurrentBlockNumber2(w3)
        except Exception as e:
            handleExpection(['W3 or lastCheckBlockNumber() or fetchCurrentBlockNumber(): ', str(e), str(datetime.utcnow())])
            continue

        trueFalse = False
        while toBlockNumber > currentBlockNumber - 5:
            time.sleep(10)
            try:
                currentBlockNumber = fetchCurrentBlockNumber2(w3)
            except Exception as e:
                handleExpection(['fetchCurrentBlockNumber() inside loop: ', str(e), str(datetime.utcnow())])
                trueFalse = True
                break

        if trueFalse:
            continue

        try:       
            contract = w3.eth.contract(address=hlp.USDT_CONTRACT_ADDRESS, abi=hlp.USDT_CONTRACT_ABI)
            transfer_event_filter = contract.events.Transfer.create_filter(fromBlock=fromBlockNumber, toBlock=toBlockNumber)
        except Exception as e:
            handleExpection(['contract or transfer_event_filter: ', str(e), str(datetime.utcnow())])
            continue

        try:
            for event in transfer_event_filter.get_all_entries():
                handle_event(event) 
        except Exception as e:
            handleExpection(['main()', str(e), str(datetime.utcnow())])
            continue

        try:
            setLastCheckBlockNumber(toBlockNumber)
        except Exception as e:
            handleExpection(['setLastCheckBlockNumber(): ', str(e), str(datetime.utcnow())])
            continue



main()

