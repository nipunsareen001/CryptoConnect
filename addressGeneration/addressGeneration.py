import csv
from datetime import datetime
import sys
import time 
from web3 import Web3, Account
import os
sys.path.insert(1,'PATH_TO_YOU_ROOT_DIRECTORY/helpers')
import helper as hlp 

def updateRecord(id, address, privateKey, approved_address):
    cursor, conn = hlp.getDatabase()
    cursor.execute(
    "EXEC UpdateMemberDepositAddress ?, ?, ?, ?, ?",
    (id, address, privateKey, datetime.utcnow(), approved_address)
    )
    conn.commit()
    hlp.closeDatabase(conn)

def generateWeb3Address():
    private_key = Web3.to_hex(os.urandom(32))
    account = Account.from_key(private_key)

    return account.address, private_key


def fetchTop100Records():
    cursor, conn = hlp.getDatabase()
    cursor.execute('EXEC FetchAndUpdateTop100MemberDepositAddresses')
    records = cursor.fetchall()
    conn.commit()
    hlp.closeDatabase(conn)
    
    return records

def sendExceptionMail(exceptionData):
    subject = 'SUBJECT'
    text_message = (
        "MESSAGE!.\r\n"
        "EXception data: .\r\n"
        +str(exceptionData[0])+str(exceptionData[1])+str(exceptionData[2])+".\r\n"
        "This email was sent through the Python script.")
                    
    hlp.send_mail(subject, text_message)

def updateExceptionLogs(exceptionData):
    with open("./addressGenerationExceptionLogs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(exceptionData)

def handleExpection(exceptionData):
    updateExceptionLogs(exceptionData)
    sendExceptionMail(exceptionData)


def updateLogs(logData):
    with open("./addressGenerationLogs.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(logData)


def main():
    while True: 
        try:
            records = fetchTop100Records()
        except Exception as e:
            handleExpection(['fetchTop100Records()', str(e), str(datetime.utcnow())])
            time.sleep(60 * 60)
            continue

        for record in records:
            id = record[0]
            try:
                address, privateKey = generateWeb3Address()
            except Exception as e:
                handleExpection(['generateWeb3Address()', str(e), str(datetime.utcnow())])
                time.sleep(60 * 60)
                continue

            try:
                approved_address = hlp.DEPOSIT_HOTWALLET_ADDRESS
                updateRecord(id, address, privateKey, approved_address)
                updateLogs(["ADDRESS SUCCESSFULLY GENERATED: ", str(id), str(address), str(datetime.utcnow())])
            except Exception as e:
                handleExpection(['updateRecord()', str(e), str(datetime.utcnow())])
                time.sleep(60 * 60)
                continue

        if(len(records)<100):
            updateLogs(["NO REcord wait for an hour", str(datetime.utcnow())])
            time.sleep(60 * 60)

if __name__ == "__main__":
    print("------------RUNNING--------------")
    main()