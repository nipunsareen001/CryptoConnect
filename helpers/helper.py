import web3
from web3.middleware import geth_poa_middleware
import pyodbc 
from enum import Enum
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib

CHAIN_ID = 97

NODE_URL = ''

TokenA_CONTRACT_ADDRESS = ''
TokenA_CONTRACT_ABI = ''

TokenB_CONTRACT_ADDRESS = TokenA_CONTRACT_ADDRESS
TokenB_CONTRACT_ABI = TokenA_CONTRACT_ABI

USDT_CONTRACT_ADDRESS = TokenB_CONTRACT_ADDRESS
USDT_CONTRACT_ABI = TokenB_CONTRACT_ABI

WITHDRAWAL_HOTWALLET_ADDRESS = ''
WITHDRAWAL_HOTWALLET_PRIVATEKEY = ''


GAS_FEE_TO_SEND_IN_WEI = 0.001 * 10**18
APPROVE_AMOUNT_WEI = 10000000000 * 10**18

#deposit address will be unique from now on
DEPOSIT_HOTWALLET_ADDRESS = WITHDRAWAL_HOTWALLET_ADDRESS
DEPOSIT_HOTWALLET_PRIVATEKEY = WITHDRAWAL_HOTWALLET_PRIVATEKEY

#development 
ALERT_HOTWALLET_BALANCE_BNB = 5 * 0.001 * 10**18
STOP_HOTWALLET_BALANCE_BNB =  3 * 0.001 * 10**18
ALERT_HOTWALLET_BALANCE_TokenA = 100000 * 10**18
STOP_HOTWALLET_BALANCE_TokenA = 100 * 10**18
ALERT_HOTWALLET_BALANCE_USDT = 1000 * 10**18
STOP_HOTWALLET_BALANCE_USDT = 10 * 10**18



# #production 
# ALERT_HOTWALLET_BALANCE_BNB = 100 * 0.001 * 10**18
# STOP_HOTWALLET_BALANCE_BNB = 20 * 0.001 * 10**18
# ALERT_HOTWALLET_BALANCE_TokenA = 100000 * 10**18
# STOP_HOTWALLET_BALANCE_TokenA = 1000 * 10**18
# ALERT_HOTWALLET_BALANCE_USDT = 1000 * 10**18
# STOP_HOTWALLET_BALANCE_USDT = 10 * 10**18

#-- SMTP INFO --
HOST = ''
PORT = 587
SENDER_EMAIL = ''
RECIVER_1_EMIAL = ''
RECIVER_2_EMIAL = ''
SMTP_USERNAME = ''
SMTP_PASSWORD = ''

# # --testing on server
# PSQL_DRIVER = ''
# PSQL_HOST = ''
# PSQL_DATABASE = ''
# PSQL_USER = ''
# PSQL_PASSWORD = ''


#-- testing on laptop
PSQL_DRIVER = ''
PSQL_HOST = ''
PSQL_DATABASE = ''
PSQL_USER = ''
PSQL_PASSWORD = ''

class TokenName(Enum):
    TokenA = 'TokenA'
    OLDTokenA = 'TokenB'
    USDT = 'USDT'
    BNB = 'BNB'

def test():
    hel = "Helppp"
    return hel

def getWeb3():
    w3 = web3.Web3(web3.HTTPProvider(NODE_URL))
    return w3


def getDatabase():
    # SQL Server
    # /opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.so.1.1
    conn = pyodbc.connect(driver=PSQL_DRIVER, host=PSQL_HOST, database=PSQL_DATABASE,
        user=PSQL_USER, password=PSQL_PASSWORD)    
    cursor = conn.cursor()
    return (cursor, conn)

def closeDatabase(conn):
    conn.close()

logger = logging.getLogger(__name__)

def send_smtp_message(
        smtp_server, smtp_username, smtp_password, sender, to_address,
        subject, text_message):

    msg = MIMEMultipart('alternative')
    msg['From'] = sender
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(text_message, 'plain'))

    smtp_server.ehlo()
    smtp_server.starttls()
    smtp_server.ehlo()
    smtp_server.login(smtp_username, smtp_password)
    smtp_server.sendmail(sender, to_address, msg.as_string())


def send_mail(subject, text_message):

    subject = "TESTING: "+ subject
    print("Sending email through SMTP server.")
    try:
        with smtplib.SMTP(HOST, PORT) as smtp_server:
            send_smtp_message(
                smtp_server, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL, RECIVER_1_EMIAL,
                 subject, text_message)
    except Exception:
        logger.exception("Couldn't send message.")
        raise
    try:
        with smtplib.SMTP(HOST, PORT) as smtp_server:
            send_smtp_message(
                smtp_server, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL, RECIVER_2_EMIAL,
                 subject, text_message)
    except Exception:
        logger.exception("Couldn't send message.")
        raise
    else:
        print("Email sent!")

