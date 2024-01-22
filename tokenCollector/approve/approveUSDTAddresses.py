import time 
from web3.middleware import geth_poa_middleware
import csv
from datetime import datetime
import sys
sys.path.insert(1,'PATH_TO_YOU_ROOT_DIRECTORY/helpers')
import helper as hlp 

TOKEN_NAME =  hlp.TokenName.USDT.value
GAS_TOKEN_NAME = hlp.TokenName.BNB.value
APPROVED_ADDRESS = hlp.DEPOSIT_HOTWALLET_ADDRESS

def updateLogs(logData):
    with open("./USDTApprovalLogs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(logData)

def updateExceptionLogs(exceptionData):
    with open("./USDTApprovalExceptionLogs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(exceptionData)

def sendAlertMail(token_name, value_str, time):
    subject = 'ALERT :USDT APPROVALS have Low '+token_name+' | BAAP NETWORK '
    text_message = (
        "USDT APPROVALS OF BAAP NETWORK WILL BE PAUSED IF "+token_name+" IS NOT RECHERGED .\r\n"
        "minimum balnce should be " +value_str+ " " + token_name + " .\r\n"
        "please transafer "+token_name+" to HOT Wallet address .\r\n"
        "UTC time: "+ time + ".\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)


def sendPausedMail(token_name, value_str, time):
    subject = 'USDT APPROVALS have been PAUSED, Low '+token_name+' | BAAP NETWORK '
    text_message = (
        "USDT APPROVALS OF BAAP NETWORK HAS BEEN PAUSED BECAUSE OF LOW "+token_name+" .\r\n"
        "minimum balnce should be " +value_str+ " " + token_name + " .\r\n"
        "paused time 15 mints, UTC time: "+ time +".\r\n"
        "please transafer "+token_name+" to HOT Wallet address, USDT APPROVALS will automatically start after 15 mints .\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)
    
def sendExceptionMail(exceptionData):
    subject = 'EXCEPTION: USDT APPROVALSL | BAAP NETWORK'
    text_message = (
        "USDT APPROVALS OF BAAP NETWORK HAS FACED AN EXCEPTION!.\r\n"
        "EXception data: .\r\n"
        +str(exceptionData[0])+str(exceptionData[1])+str(exceptionData[2])+".\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)


def handleExpection(exceptionData):
    updateExceptionLogs(exceptionData)
    sendExceptionMail(exceptionData)


def fetchNonApprovedAddress():
    cursor, conn = hlp.getDatabase()
    cursor.execute('EXEC FetchForApproval ?', (TOKEN_NAME))
    addressInfo = cursor.fetchall()
    conn.commit()
    hlp.closeDatabase(conn)
    return addressInfo

def checkEnoughGas(w3):
    hotWallet_BNB_balance =  w3.eth.get_balance(APPROVED_ADDRESS)
    
    if(hotWallet_BNB_balance >= hlp.ALERT_HOTWALLET_BALANCE_BNB):
        return True
    elif((hotWallet_BNB_balance < hlp.ALERT_HOTWALLET_BALANCE_BNB) & (hotWallet_BNB_balance >= hlp.STOP_HOTWALLET_BALANCE_BNB)):
        alert_BNB = hlp.ALERT_HOTWALLET_BALANCE_BNB / 10 ** 18
        sendAlertMail('BNB', str(alert_BNB), str(datetime.utcnow()))
        updateLogs(['Alert: LOW BNB, less then -> ', str(alert_BNB), str(datetime.utcnow())])
        return True
    else:
        stop_BNB = hlp.STOP_HOTWALLET_BALANCE_BNB / 10 ** 18
        sendPausedMail('BNB', str(stop_BNB), str(datetime.utcnow()))
        updateLogs(['Withdraw Paused: LOW BNB, less then -> ', str(stop_BNB), str(datetime.utcnow())])
        return False
    

def setApprovalStatus(id, approved_status):
    cursor, conn = hlp.getDatabase()
    cursor.execute('ResetApprovalStatus ? ? ?',(TOKEN_NAME, id, approved_status))
    conn.commit()
    hlp.closeDatabase(conn)


def transfer_bnb(w3, to_address, bnb_value):
    nonce = w3.eth.get_transaction_count(APPROVED_ADDRESS)

    # Convert BNB value to Wei
    value_wei = w3.toWei(bnb_value, 'ether')

    txn = {
        'chainId': hlp.CHAIN_ID,
        'to': to_address,
        'value': value_wei,  # Value in Wei
        'gas': 2000000,
        'gasPrice': w3.toWei(20, 'gwei'),  # Gas price in Wei
        'nonce': nonce,
    }

    signed_txn = w3.eth.account.sign_transaction(txn, hlp.DEPOSIT_HOTWALLET_PRIVATEKEY)
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return txn_hash


def checkTransactionReceipt(w3, txn_hash):
    time.sleep(30)
    try: 
        receipt = w3.eth.get_transaction_receipt(txn_hash)
    except:
        time.sleep(150)
        receipt = w3.eth.get_transaction_receipt(txn_hash)

    if receipt.status == 1:
        transaction_successful = True

        # Fetch the original transaction to get the gas price
        txn = w3.eth.get_transaction(txn_hash)

        # Calculate the gas fee
        gas_fee_wei = txn['gasPrice'] * receipt.gasUsed
        gas_fee_bnb = w3.fromWei(gas_fee_wei, 'ether')  # Convert from Wei to BNB

        return transaction_successful, gas_fee_bnb
    else:
        transaction_successful = False

        return transaction_successful, 0

    
def updateApprovedStatusAndLogTrx(id, txn_hash, from_address, to_address, token_name_transfered, token_name_approved, transacion_reason, gas_fee_bnb, token_value, transaction_time, approved_status):
    cursor, conn = hlp.getDatabase()
    cursor.execute('EXEC AddDepositLogAndUpdateStatus ? ? ? ? ? ? ? ? ? ? ? ',(id, txn_hash, from_address, to_address, token_name_transfered, token_name_approved, transacion_reason, gas_fee_bnb, token_value, transaction_time, approved_status))
    conn.commit()
    hlp.closeDatabase(conn)


def approveToken(w3, token_name, token_amount_wei, user_address, user_private_key):
    spender_address = APPROVED_ADDRESS
    # Mapping of token names to their contract addresses and ABIs
    token_contracts = {
        'USDT': {'address': hlp.USDT_CONTRACT_ADDRESS, 'abi': hlp.USDT_CONTRACT_ABI},
        'TokenB': {'address': hlp.TokenB_CONTRACT_ADDRESS, 'abi': hlp.TokenB_CONTRACT_ABI},
        'TokenA': {'address': hlp.TokenA_CONTRACT_ADDRESS, 'abi': hlp.TokenA_CONTRACT_ABI}
    }

    # Select the correct contract based on token_name
    if token_name in token_contracts:
        contract_info = token_contracts[token_name]
        contract = w3.eth.contract(address=contract_info['address'], abi=contract_info['abi'])
    else:
        raise ValueError("Invalid token name provided")

    # Calculate nonce for transaction
    nonce = w3.eth.get_transaction_count(user_address)

    # Convert amount to correct format (usually the token's smallest unit, like Wei for ETH

    # Build transaction for the approve function
    txn = contract.functions.approve(spender_address, token_amount_wei).build_transaction({
        'chainId': hlp.CHAIN_ID,
        'gas': 2000000,
        'gasPrice': w3.toWei(20, 'gwei'),
        'nonce': nonce,
    })

    # Sign the transaction with the sender's private key
    signed_txn = w3.eth.account.sign_transaction(txn, user_private_key)

    # Send the transaction
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return txn_hash

def fetchPrivateKeyOfUser(address):
    cursor, conn = hlp.getDatabase()
    cursor.execute('select nvc_private_key from member_deposit_address where nvc_address = ?', (address))
    userInfo = cursor.fetchall()
    conn.commit()
    hlp.closeDatabase(conn)
    privkey = userInfo[0][0]
    return privkey


def transfer_remaning_bnb(w3, from_address, from_private_key, to_address):
    # Initialize Web3

    # Get the balance of the from_address
    balance_wei = w3.eth.get_balance(from_address)

    # Estimate gas price
    gas_price = w3.eth.gas_price  # Or use w3.eth.generate_gas_price() for dynamic pricing

    # Set a reasonable gas limit for a simple transfer (21000 is standard for ETH, similar for BNB)
    gas_limit = 21000

    # Estimate the gas fee
    gas_fee = gas_limit * gas_price

    # Calculate the amount to transfer (balance minus the gas fee)
    amount_to_send = balance_wei - gas_fee

    # If the balance is not enough to cover the gas fee, raise an error
    if amount_to_send <= 0:
        raise ValueError("Insufficient balance to cover gas fees.")

    # Build transaction
    txn = {
        'chainId': hlp.CHAIN_ID,
        'to': to_address,
        'value': amount_to_send,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'nonce': w3.eth.get_transaction_count(from_address),
    }

    # Sign transaction
    signed_txn = w3.eth.account.sign_transaction(txn, from_private_key)

    # Send transaction
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return txn_hash, amount_to_send


def main(): 
    try:
        addressInfo = fetchNonApprovedAddress()
    except Exception as e:
        handleExpection(['fetchNonApprovedAddress(): ', str(e), str(datetime.utcnow())])
        # wait for 15 mints because of exception
        time.sleep(15 * 60)
        return

    if len(addressInfo) > 0 :
        addressBody = addressInfo[0]
        id = addressBody[0]
        address = addressBody[1]

        w3 = hlp.getWeb3()
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        try:
            enoughGas = checkEnoughGas(w3)
        except Exception as e:
            approved_status = 0
            setApprovalStatus(id, approved_status)
            handleExpection(['checkEnoughGas(): ', str(e), str(datetime.utcnow())])
            # wait for 15 mints because of exception
            time.sleep(15 * 60)
            return
        
        if(enoughGas):
            # transfer gas to address, then verify, then save
            try:
                txn_hash = transfer_bnb(w3, address, hlp.GAS_FEE_TO_SEND_IN_WEI)
            except Exception as e:
                handleExpection(['transfer_bnb(): ', str(e), str(datetime.utcnow())])
                # wait for 15 mints because of exception
                time.sleep(15 * 60)
                return

            try: 
                status, gas_fee_bnb = checkTransactionReceipt(w3, txn_hash)
            except Exception as e:
                handleExpection(['checkTransactionReceipt() on transfer_bnb', str(e), str(datetime.utcnow())])       
                # wait for 15 mints because of exception
                time.sleep(15 * 60)
                return
            
            if(status):
                try: 
                    approved_status = 2
                    transaction_reason = "TRNASFER_BNB"
                    updateApprovedStatusAndLogTrx(id, txn_hash, APPROVED_ADDRESS, address, GAS_TOKEN_NAME, TOKEN_NAME, transaction_reason, gas_fee_bnb, hlp.GAS_FEE_TO_SEND_IN_WEI, datetime.utcnow(), approved_status)
                    updateLogs(["BNB transfered succefsully: " + + "id: " + str(id), str(datetime.utcnow())])

                except Exception as e:
                    handleExpection(['updateApprovedStatusAndLogTrx() on TRNASFER_BNB ', str(e), str(datetime.utcnow())])       
                    # wait for 15 mints because of exception
                    time.sleep(15 * 60)
                    return 
                try:
                    privKey = fetchPrivateKeyOfUser(address)
                except Exception as e:
                    handleExpection(['fetchPrivateKeyOfUser : ', str(e), str(datetime.utcnow())])       
                    # wait for 15 mints because of exception
                    time.sleep(15 * 60)
                    return   
                
                try:
                    txn_hash = approveToken(w3, TOKEN_NAME, hlp.APPROVE_AMOUNT_WEI, address, privKey)
                except Exception as e:
                    handleExpection(['approveToken : ', str(e), str(datetime.utcnow())])       
                    # wait for 15 mints because of exception
                    time.sleep(15 * 60)
                    return   85
                
                try:
                    status, gas_fee_bnb = checkTransactionReceipt(w3, txn_hash)

                except Exception as e:
                    handleExpection(['checkTransactionReceipt() on approveToken', str(e), str(datetime.utcnow())])       
                    # wait for 15 mints because of exception
                    time.sleep(15 * 60)
                    return
                
                if(status):
                    try: 
                        approved_status = 3
                        transaction_reason = "APPROVE_ADDRESS"
                        updateApprovedStatusAndLogTrx(id, txn_hash, address, APPROVED_ADDRESS, TOKEN_NAME, TOKEN_NAME, transaction_reason, gas_fee_bnb, hlp.APPROVE_AMOUNT_WEI, datetime.utcnow(), approved_status)
                        updateLogs(["Addressd Approved Succefsully: " + + "id: " + str(id), str(datetime.utcnow())])

                    except Exception as e:
                        handleExpection(['updateApprovedStatusAndLogTrx() on  APPROVE_ADDRESS', str(e), str(datetime.utcnow())])       
                        # wait for 15 mints because of exception
                        time.sleep(15 * 60)
                        return 
                    
                    try:
                        txn_hash, amount_to_send_wei = transfer_remaning_bnb(w3, address, privKey, APPROVED_ADDRESS)
                    except Exception as e:
                        handleExpection(['transfer_remaning_bnb : ', str(e), str(datetime.utcnow())])       
                        # wait for 15 mints because of exception
                        time.sleep(15 * 60)
                        return      

                    try:
                        status, gas_fee_bnb = checkTransactionReceipt(w3, txn_hash)  

                    except Exception as e:
                        handleExpection(['checkTransactionReceipt() on transfer_remaning_bnb', str(e), str(datetime.utcnow())])       
                        # wait for 15 mints because of exception
                        time.sleep(15 * 60)
                        return
                    
                    if(status):
                        try:
                            approved_status = 4
                            transaction_reason = "TRANFER_REMAING_BNB"
                            updateApprovedStatusAndLogTrx(id, txn_hash, address, APPROVED_ADDRESS, TOKEN_NAME, TOKEN_NAME, transaction_reason, gas_fee_bnb, (amount_to_send_wei/10**18), datetime.utcnow(), approved_status)
                            updateLogs(["Addressd Approved Succefsully: " + + "id: " + str(id), str(datetime.utcnow())])
                        except Exception as e:
                            handleExpection(['updateApprovedStatusAndLogTrx() on  TRANFER_REMAING_BNB', str(e), str(datetime.utcnow())])       
                            # wait for 15 mints because of exception
                            time.sleep(15 * 60)
                            return 

            
            else:
                approved_status = 0
                setApprovalStatus(id, approved_status)
            

        else:
            approved_status = 0
            setApprovalStatus(id, approved_status)
            updateLogs(["Not enough gas wait for 15 minuts at: ", str(datetime.utcnow())])
            #not enough gas wait for 15 minuts
            time.sleep(15 * 60)


    else:
        updateLogs(["No address to approve in DB, paused of 24 hours at: ", str(datetime.utcnow())])
        #there are no address to approve so wait for 24 hours
        time.sleep(24 * 60 * 60)


if __name__ == "__main__":
    print("------------RUNNING--------------")
    while(True):

        #main script will run continiusly
        try:
            main()
        except Exception as e:
            handleExpection(['main(): ', str(e), str(datetime.utcnow())])
            # wait for 15 mints because of exception
            time.sleep(15 * 60)