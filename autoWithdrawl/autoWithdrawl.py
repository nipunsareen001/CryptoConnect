import time 
from web3.middleware import geth_poa_middleware
import csv
from datetime import datetime
import sys
sys.path.insert(1,'PATH_TO_YOU_ROOT_DIRECTORY/helpers')
import helper as hlp 


def checkEnoughGas(w3):
    hotWallet_BNB_balance =  w3.eth.get_balance(hlp.WITHDRAWAL_HOTWALLET_ADDRESS)
    
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


def checkEnoughTokenA(TokenA_contract, token_value_wei):
    hotWallet_TokenA_balance = TokenA_contract.functions.balanceOf(hlp.WITHDRAWAL_HOTWALLET_ADDRESS).call()


    if(((hotWallet_TokenA_balance >= hlp.ALERT_HOTWALLET_BALANCE_TokenA)) & (hotWallet_TokenA_balance  >= token_value_wei)):
        return True
    elif((hotWallet_TokenA_balance  < token_value_wei)):
        sendPausedMail('TokenA', str(token_value_wei), str(datetime.utcnow()))
        updateLogs(['STOP: LOW TokenA, less then token value -> ', str(token_value_wei), str(datetime.utcnow())])
        return False
    elif(((hotWallet_TokenA_balance < hlp.ALERT_HOTWALLET_BALANCE_TokenA))):
        minimum_TokenA = hlp.ALERT_HOTWALLET_BALANCE_TokenA / 10 ** 18
        if((hotWallet_TokenA_balance >= hlp.STOP_HOTWALLET_BALANCE_TokenA)):
            sendAlertMail('TokenA', str(minimum_TokenA), str(datetime.utcnow()))
            updateLogs(['Alert: LOW TokenA, less then alert-> ', str(minimum_TokenA), str(datetime.utcnow())])
            return True
        else:
            sendPausedMail('TokenA', str(minimum_TokenA), str(datetime.utcnow()))
            updateLogs(['STOP: LOW TokenA, less then alert -> ', str(minimum_TokenA), str(datetime.utcnow())])
            return False


def checkEnoughUSDT(USDT_contract, token_value_wei):
    hotWallet_USDT_balance = USDT_contract.functions.balanceOf(hlp.WITHDRAWAL_HOTWALLET_ADDRESS).call()

    if(((hotWallet_USDT_balance >= hlp.ALERT_HOTWALLET_BALANCE_USDT)) & (hotWallet_USDT_balance  >= token_value_wei)):
        return True
    elif((hotWallet_USDT_balance  < token_value_wei)):
        sendPausedMail('USDT', str(token_value_wei), str(datetime.utcnow()))
        updateLogs(['STOP: LOW USDT, less then token value -> ', str(token_value_wei), str(datetime.utcnow())])
        return False
    elif(((hotWallet_USDT_balance < hlp.ALERT_HOTWALLET_BALANCE_USDT))):
        minimum_USDT = hlp.ALERT_HOTWALLET_BALANCE_USDT / 10 ** 18
        if((hotWallet_USDT_balance >= hlp.STOP_HOTWALLET_BALANCE_USDT)):
            sendAlertMail('USDT', str(minimum_USDT), str(datetime.utcnow()))
            updateLogs(['Alert: LOW USDT, less then alert-> ', str(minimum_USDT), str(datetime.utcnow())])
            return True
        else:
            sendPausedMail('USDT', str(minimum_USDT), str(datetime.utcnow()))
            updateLogs(['STOP: LOW USDT, less then alert -> ', str(minimum_USDT), str(datetime.utcnow())])
            return False
    

def transferTokenACoin(w3, TokenA_contract, user_address, token_value):
    nonce = w3.eth.get_transaction_count(hlp.WITHDRAWAL_HOTWALLET_ADDRESS)

    # amountToSend = token_value * 10**18
    token_value_int = int(round(token_value))
    txn = TokenA_contract.functions.transfer(user_address, token_value_int).build_transaction({
        'chainId': hlp.CHAIN_ID,
        'gas': 2000000,
        'gasPrice': 20 * 10**9,  # 20 gwei in wei
        'nonce': nonce,
    })
    signed_txn = w3.eth.account.sign_transaction(txn, hlp.WITHDRAWAL_HOTWALLET_PRIVATEKEY)
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return txn_hash

def transferUSDTCoin(w3, USDT_contract, user_address, token_value):
    nonce = w3.eth.get_transaction_count(hlp.WITHDRAWAL_HOTWALLET_ADDRESS)
    # amountToSend = token_value * 10**18
    token_value_int = int(round(token_value))
    txn = USDT_contract.functions.transfer(user_address, token_value_int).build_transaction({
        'chainId': hlp.CHAIN_ID,
        'gas': 2000000,
        'gasPrice': 20 * 10**9,  # 20 gwei in wei
        'nonce': nonce,
    })
    signed_txn = w3.eth.account.sign_transaction(txn, hlp.WITHDRAWAL_HOTWALLET_PRIVATEKEY)
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return txn_hash


def checkTransactionRecipt(w3, txn_hash):
    time.sleep(30)
    try: 
        receipt = w3.eth.get_transaction_receipt(txn_hash)
    except:
        time.sleep(150)
        receipt = w3.eth.get_transaction_receipt(txn_hash)

    if receipt.status == 1:
        return True
    else:
        return False
    
def fetchWithdrawal():
    cursor, conn = hlp.getDatabase()
    cursor.execute('EXEC NewWithdrawalsForAutoTransfer')
    withdraw_requests = cursor.fetchall()
    conn.commit()
    hlp.closeDatabase(conn)
    return withdraw_requests

def setAutoWithdrawalStatusToZero(id):
    cursor, conn = hlp.getDatabase()
    cursor.execute('update member_withdraw_request set auto_withdrawal_status = 0 where id = ?',(id))
    conn.commit()
    hlp.closeDatabase(conn)

def insertBlockchainWithdrawlogsWithEX(e, id, txn_hash):
    cursor, conn = hlp.getDatabase()

    if(txn_hash != ''):
        cursor.execute('insert into Blockchain_Withdraw_logs(member_withdraw_id, transaction_hash, exception, withdraw_time) values(?, ?, ?, ?)', (id, txn_hash, str(e), datetime.utcnow()))
        conn.commit()
    else:
        cursor.execute('insert into Blockchain_Withdraw_logs(member_withdraw_id, exception, withdraw_time) values(?, ?, ?)', (id, str(e), datetime.utcnow()))
        conn.commit()
    
    hlp.closeDatabase(conn)
    
def updateWithdrawalWithSuccess(txn_hash, id, token_type, token_value, user_address):

    value_trx_str = str(token_value * 10 **18)

    token_type_name = ''
    if(token_type == 1):
        token_type_name = hlp.TokenName.TokenA.value
    if(token_type == 2):
        token_type_name = hlp.TokenName.USDT.value

    cursor, conn = hlp.getDatabase()
    cursor.execute(
    "EXEC ProcessWithdrawal ?, ?, ?, ?, ?, ?, ?, ?, ?",
    (id, txn_hash.hex(), hlp.WITHDRAWAL_HOTWALLET_ADDRESS, user_address, token_value, value_trx_str, token_type_name, datetime.utcnow(), 1)
    )
    conn.commit()
    hlp.closeDatabase(conn)


def updateLogs(logData):
    with open("./withdrawlLogs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(logData)

def updateExceptionLogs(exceptionData):
    with open("./withdrawlExceptionLogs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(exceptionData)

def sendAlertMail(token_name, value_str, time):
    subject = 'ALERT :AUTO-WITHDRAWL Low '+token_name
    text_message = (
        "AUTO-WITHDRAWL WILL BE PAUSED IF "+token_name+" IS NOT RECHERGED .\r\n"
        "minimum balnce should be " +value_str+ " " + token_name + " .\r\n"
        "please transafer "+token_name+" to HOT Wallet address .\r\n"
        "UTC time: "+ time + ".\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)


def sendPausedMail(token_name, value_str, time):
    subject = 'AUTO-WITHDRAWL PAUSED Low '+token_name
    text_message = (
        "AUTO-WITHDRAWL HAS BEEN PAUSED BECAUSE OF LOW "+token_name+" .\r\n"
        "minimum balnce should be " +value_str+ " " + token_name + " .\r\n"
        "paused time 1 hour, UTC time: "+ time +".\r\n"
        "please transafer "+token_name+" to HOT Wallet address, AUTO-WITHDRAWL will automatically start after an hour .\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)
    
def sendExceptionMail(exceptionData):
    subject = 'EXCEPTION: AUTO-WITHDRAWL'
    text_message = (
        "AUTO-WITHDRAWL HAS FACED AN EXCEPTION!.\r\n"
        "EXception data: .\r\n"
        +str(exceptionData[0])+str(exceptionData[1])+str(exceptionData[2])+".\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)


def handleExpection(exceptionData):
    updateExceptionLogs(exceptionData)
    sendExceptionMail(exceptionData)



def main(): 
    try:    
        withdrawals = fetchWithdrawal()
    except Exception as e:
        handleExpection(['fetchWithdrawal(): ', str(e), str(datetime.utcnow())])
        return

    if len(withdrawals) > 0 :
        w3 = hlp.getWeb3()
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        try:
            enoughGas = checkEnoughGas(w3)
        except Exception as e:
            setAutoWithdrawalStatusToZero(withdrawals[0][0])
            handleExpection(['checkEnoughGas(): ', str(e), str(datetime.utcnow())])
            return
        
        if(enoughGas):
            withdrawal_body = withdrawals[0]

            id = withdrawal_body[0]
            token_type = withdrawal_body[1]
            token_value = withdrawal_body[2]
            user_address = w3.to_checksum_address(withdrawal_body[3])

            token_value_wei = token_value * 10**18

            # 1 -> TokenA 
            if(token_type == 1):
                TokenA_contract = w3.eth.contract(address=hlp.TokenA_CONTRACT_ADDRESS, abi=hlp.TokenA_CONTRACT_ABI)
                try:
                    enoughTokenA = checkEnoughTokenA(TokenA_contract, token_value_wei)
                except Exception as e:
                    setAutoWithdrawalStatusToZero(id)
                    handleExpection(['checkEnoughTokenA(): ', str(e), str(datetime.utcnow())])
                    return

                if(enoughTokenA):
                    try:
                        txn_hash = transferTokenACoin(w3, TokenA_contract, user_address, token_value_wei) 
                    except Exception as e:
                        insertBlockchainWithdrawlogsWithEX(e, id, '')
                        handleExpection(['transferTokenACoin(): ', str(e), str(datetime.utcnow())])
                        return

                    try: 
                        status = checkTransactionRecipt(w3, txn_hash)
                        if(status):
                            updateWithdrawalWithSuccess(txn_hash, id, token_type, token_value, user_address)
                            updateLogs(["WITHDRAWAL SUCCESSFULL: " + str(token_type) + "id: " + str(id), str(datetime.utcnow())])
                        else:
                            setAutoWithdrawalStatusToZero(id)
                    except Exception as e:
                        insertBlockchainWithdrawlogsWithEX(e, id, txn_hash)
                        handleExpection(['checkTransactionRecipt() or DBfun(): ', str(e), str(datetime.utcnow())])       
                        return
                       
                else:
                    setAutoWithdrawalStatusToZero(id)

                    #not enough TokenA wait for  15 minuts
                    time.sleep(15 * 60)
    
            # 2 -> USDT
            elif(token_type == 2):
                USDT_contract = w3.eth.contract(address=hlp.USDT_CONTRACT_ADDRESS, abi=hlp.USDT_CONTRACT_ABI)
                try:
                    enoughUSDT = checkEnoughUSDT(USDT_contract, token_value_wei)
                except Exception as e:
                    setAutoWithdrawalStatusToZero(id)
                    handleExpection(['checkEnoughUSDT(): ', str(e), str(datetime.utcnow())]) 
                    return

                if(enoughUSDT):
                    try:
                        txn_hash = transferUSDTCoin(w3, USDT_contract, user_address, token_value_wei) 
                    except Exception as e:
                        insertBlockchainWithdrawlogsWithEX(e, id, '')
                        handleExpection(['transferUSDTCoin(): ', str(e), str(datetime.utcnow())]) 
                        return

                    try: 
                        status = checkTransactionRecipt(w3, txn_hash)
                        if(status):
                            updateWithdrawalWithSuccess(txn_hash, id, token_type, token_value, user_address)
                            updateLogs(["WITHDRAWAL SUCCESSFULL: " + str(token_type) + "id: " + str(id), str(datetime.utcnow())])
                        else:
                            setAutoWithdrawalStatusToZero(id)
                    except Exception as e:
                        insertBlockchainWithdrawlogsWithEX(e, id, txn_hash)
                        handleExpection(['checkTransactionRecipt() or DBfun(): ', str(e), str(datetime.utcnow())]) 
                        return
                    
                else:
                    setAutoWithdrawalStatusToZero(id)

                    #not enough USDT wait for  15 minuts
                    time.sleep(15 * 60)
            else:
                updateLogs(["WRONG token_type: " + str(token_type) + "id: " + str(id), str(datetime.utcnow())])


        else:
            setAutoWithdrawalStatusToZero(withdrawals[0][0])

            #not enough gas wait for 15 minuts
            time.sleep(15 * 60)
   
    else:
        updateLogs(["No Withdrawal in DB wait paused of 15 minuts: ", str(datetime.utcnow())])

        #there are no withdrawal so wait for 15 minuts
        time.sleep(15 * 60)
        


if __name__ == "__main__":
    print("------------RUNNING--------------")
    while(True):

        #main script will run continiusly
        try:
            main()
        except Exception as e:
            handleExpection(['main(): ', str(e), str(datetime.utcnow())])

        
        
        