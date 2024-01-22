import time 
from web3.middleware import geth_poa_middleware
import csv
from datetime import datetime
import sys
sys.path.insert(1,'PATH_TO_YOU_ROOT_DIRECTORY/helpers')
import helper as hlp 


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
    subject = 'ALERT :USDT APPROVALS have Low '+token_name
    text_message = (
        "USDT APPROVALS  WILL BE PAUSED IF "+token_name+" IS NOT RECHERGED .\r\n"
        "minimum balnce should be " +value_str+ " " + token_name + " .\r\n"
        "please transafer "+token_name+" to HOT Wallet address .\r\n"
        "UTC time: "+ time + ".\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)


def sendPausedMail(token_name, value_str, time):
    subject = 'USDT APPROVALS have been PAUSED, Low '+token_name
    text_message = (
        "USDT APPROVALS OF HAS BEEN PAUSED BECAUSE OF LOW "+token_name+" .\r\n"
        "minimum balnce should be " +value_str+ " " + token_name + " .\r\n"
        "paused time 15 mints, UTC time: "+ time +".\r\n"
        "please transafer "+token_name+" to HOT Wallet address, USDT APPROVALS will automatically start after 15 mints .\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)
    
def sendExceptionMail(exceptionData):
    subject = 'EXCEPTION: USDT APPROVALSL '
    text_message = (
        "USDT APPROVALS OF HAS FACED AN EXCEPTION!.\r\n"
        "EXception data: .\r\n"
        +str(exceptionData[0])+str(exceptionData[1])+str(exceptionData[2])+".\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)


def handleExpection(exceptionData):
    updateExceptionLogs(exceptionData)
    sendExceptionMail(exceptionData)


def fetchApprovedAddress():
    cursor, conn = hlp.getDatabase()
    cursor.execute('EXEC  ?', ())
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


def main():

    # address, approve_status + balance of (usdt, TokenA, TokenB) fetchApprovedAddress()
    
    # if (usdt)
    # if (TokenB)
    # if (dhnau)


    #checkEnoughGas()

    #trsanferFrom()

    #checkTransactionReceipt()

    #updateTransferFromStatusAndLogTrx

    try:
        addressInfo = fetchApprovedAddress()
    except Exception as e:
        handleExpection(['fetchApprovedAddress(): ', str(e), str(datetime.utcnow())])
        # wait for 15 mints because of exception
        time.sleep(15 * 60)

    if len(addressInfo) > 0 :

        addressBody = addressInfo[0]
        id = addressBody[0]

        w3 = hlp.getWeb3()
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        try:
            enoughGas = checkEnoughGas(w3)
        except Exception as e:
            approved_status = 0
            # setCentralTransferStatusToZero(id, token_name)
            handleExpection(['checkEnoughGas(): ', str(e), str(datetime.utcnow())])
            # wait for 15 mints because of exception
            time.sleep(15 * 60)
            return
        

        usdt_balance = addressBody[1]
        TokenA_balance = addressBody[2]
        TokenB_balance = addressBody[3]
        usdt_approved_status = addressBody[4]
        TokenA_approved_status = addressBody[5]
        TokenB_approved_status = addressBody[6]
        address = addressBody[7]



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