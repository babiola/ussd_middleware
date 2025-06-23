import requests
import re
import locale
import binascii
from random import randint
import uuid
import logging
import json
import time
import base64
import bcrypt
from typing import List
from fastapi import Request
from functools import lru_cache
from typing import Union

from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from enum import Enum as PythonEnum
from jose import jwt, JWTError
from passlib.context import CryptContext
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from schemas.setting import Setting,AppSetting
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import os
import base64
from schemas.bank import Bank
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates/email")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_response(url,method=None,body=None,headers=None,status_code=500, message="Service Unavailable"):
    response = requests.Response()
    headers = headers or {"content-type": "application/json"}
    method = method or "GET"
    request = requests.Request(method, url, headers=headers, data=body).prepare()
    response.status_code = status_code
    response._content = json.dumps({"statusCode":str(status_code),"statusDescription":message,}).encode()  # Encode message as bytes
    response.headers = headers
    response.request = request
    return response
def http(url, params={}, headers={"content-type": "application/json"},contentType="json",method="GET",files=None,timeout=10):
    print("INFO|%s|%s|%s" % (str(http.__name__), str(url), str(params)))
    startTime = datetime.now()
    try:
        if len(params) > 0:
            if contentType =="formData":
                print("am here")
                resp = requests.post(url, data = params,files=files,timeout=timeout)
            else:
                resp = requests.post(url, data = json.dumps(params), headers=headers, timeout=timeout)
        else:
            if method=="POST":
                resp = requests.post(url,headers=headers,timeout=timeout)
            else:
                resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.Timeout:
        print("Request timed out.")
        resp =  create_response(url=url,method=method,body=params,headers=headers,status_code=408,message="Request timed out.")
    except requests.ConnectionError:
        print("Connection error.")
        resp =  create_response(url=url,method=method,body=params,headers=headers,status_code=503,message="Connection error try again later")
    except requests.RequestException as e:
        resp = create_response(url=url,method=method,body=params,headers=headers,status_code=500,message="System busy try again later")
    endTime = datetime.now()
    responseTime = (endTime - startTime).total_seconds()
    text = "_URL:: %s,_HEADER:: %s, _PARAM:: %s, _RESPONSE:: %s _STATUSCODE:: %s _TIME:: %s " % (
        str(resp.request.url),
        str(resp.request.headers),
        str(resp.request.body),
        str(resp.content),
        str(resp.status_code),
        str(responseTime),
    )
    print(text)
    return resp
def validateIPs(request: Request, allowed: List[str]):
    logger.info(f"this is a request coming from {request.headers} allowed IPs are {str(allowed)} client host {request.client}")
    forwarded = request.headers.get("X-Forwarded-For")
    logger.info(f"this is a request coming from IP ............{forwarded}")
    #client_ip = forwarded.split(",")[0] if forwarded else request.client.host
    clientIp = forwarded if forwarded else request.client.host
    if clientIp in allowed:
        return True
    return False
def validateIP(request: Request, allowed: List[str]):
    logger.info(f"this is a request coming from {request}")
    forwarded = request.headers.get("X-Forwarded-For")
    logger.info(f"this is a request coming from IP ............{forwarded}")
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip_list = [ip.strip() for ip in x_forwarded_for.split(",")]
        return any(ip in allowed for ip in ip_list)
    elif request.client.host in allowed:
        return True
    return False
def has_consecutive_or_repeating_digits(pin: str, min_streak: int = 3) -> bool:
    if not pin.isdigit() or len(pin) < min_streak:
        return False

    count = 1

    for i in range(1, len(pin)):
        prev = int(pin[i - 1])
        curr = int(pin[i])

        # Check ascending or descending
        if curr == prev + 1 or curr == prev - 1 or curr == prev:
            count += 1
            if count >= min_streak:
                return True
        else:
            count = 1

    return False
def validateBVNDateOfBirth(bvnDob:str,inputDob:str)->bool:
    try:
        date_obj = datetime.strptime(bvnDob, "%d-%b-%Y")
        return date_obj.strftime("%Y%m%d") == inputDob
    except Exception as ex:
        return False
def checkPin(key:str,pin:str):
    if pin:
        decryptPin = decrypt_pin(encryptedPin=pin,key=key)
        logger.info(f"this is the decrptyed PIN .........{decryptPin}")
        if decryptPin and decryptPin.isdigit() and len(decryptPin) == 4:
            logger.info(f"this is the decrptyed PIN .........{decryptPin}")
            return decryptPin
        return None
    return None
def encrypt_pin(plaintextPin: str,key:str) -> str:
    key = bytes.fromhex(key)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for AESGCM
    encrypted = aesgcm.encrypt(nonce, plaintextPin.encode(), None)
    return base64.b64encode(nonce + encrypted).decode()
def decrypt_pin(encryptedPin: str,key:str) -> str:
    key = bytes.fromhex(key)
    aesgcm = AESGCM(key)
    decoded = base64.b64decode(encryptedPin)
    nonce = decoded[:12]
    ciphertext = decoded[12:]
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted.decode()
def amountToKobo(amount:str)->str:
    return str(int(float(amount) * 100))
def mailer(body, setting: Setting, subject: str, toAddress: str, fileToSend=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = setting.mail_from
        msg["To"] = toAddress
        msg["Subject"] = subject
        msg.preamble = subject
        msg.attach(MIMEText(body, "html"))
        if fileToSend:
            ctype, encoding = mimetypes.guess_type(fileToSend)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"

            maintype, subtype = ctype.split("/", 1)
            if maintype == "text":
                fp = open(fileToSend)
                # Note: we should handle calculating the charset
                attachment = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == "image":
                fp = open(fileToSend, "rb")
                attachment = MIMEImage(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == "audio":
                fp = open(fileToSend, "rb")
                attachment = MIMEAudio(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(fileToSend, "rb")
                attachment = MIMEBase(maintype, subtype)
                attachment.set_payload(fp.read())
                fp.close()
                encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition", "attachment", filename=fileToSend
            )
            msg.attach(attachment)
        logger.info(f"sending mail to {toAddress} at {str(datetime.now())}")
        server = smtplib.SMTP(f"{setting.mail_server}:{setting.mail_port}")
        server.starttls()
        server.login(setting.mail_username, setting.mail_password)
        server.sendmail(setting.mail_from, toAddress, msg.as_string())
        # server.quit()
    except Exception as e:
        logger.error(f"Error sending email at {datetime.now()} {str(e)}")
        pass
def send_sms_message(setting: Setting, toPhoneNumber: str, message: str,transactionId:str):
    try:
        logger.info(f"started sending SMS to {toPhoneNumber} with text {message} with transactionId {transactionId}")
        payload ={
            "sms": {
                "dest":toPhoneNumber,
                "referenceId":transactionId,
                "src": setting.senderid,
                "text": message,
                "unicode": True
                },
                "account": {
                    "password":setting.vanso_password,
                    "systemId":setting.vanso_username
                    }
            }
        response = http(url=setting.vanso_url,params=payload)
        if response.status_code == 200:
            return True
        return False
    except Exception as ex:
        logger.error(str(ex))
        pass
def formatPhoneFull(msisdn):
    msisdn = msisdn.replace("+", "", 1)
    if msisdn.startswith("234") and len(msisdn) == 13:
        return msisdn
    elif msisdn.startswith("0") and len(msisdn) == 11:
        return msisdn.replace("0", "234", 1)
    elif len(msisdn) == 10:
        return f"234{msisdn}"
    else:
        return msisdn
def formatPhone(msisdn:str)->str:
    msisdn = msisdn.replace("+", "", 1)
    if msisdn.startswith("234") and len(msisdn) == 13:
        return msisdn.replace("234", "0", 1)
    elif not msisdn.startswith("0") and len(msisdn) == 10:
        return f"0{msisdn}"
    elif msisdn.startswith("0") and len(msisdn) == 11:
        return msisdn
    else:
        return msisdn
def formatPhoneShort(msisdn:str)->str:
    msisdn = msisdn.replace("+", "", 1)
    if msisdn.startswith("234") and len(msisdn) == 13:
        return msisdn.replace("234", "", 1)  #
    elif msisdn.startswith("0") and len(msisdn) == 11:
        return msisdn.replace("0", "", 1)
    else:
        return msisdn
def get_bank_by_code(bankcode: str, banks: List[Bank]) -> Union[Bank, None]:
    return next((bank for bank in banks if bank.Code == bankcode), None)
def mask_email(email):
    return re.sub(r'^[^@]+', '*' * len(re.search(r'^[^@]+', email).group()), email)

def generateId():
    return str(int(time.time()))


def generateOTP():
    return str(randint(100000, 999999))


def generateUniqueId():
    return "2510" + str(uuid.uuid5(uuid.NAMESPACE_DNS, "payvantage-ng.com").int)

def formatDateOfBirth(dob:str):
    try:
        input_date = datetime.strptime(dob, "%d-%b-%y")
        return input_date.strftime("%d%m%Y")
    except Exception as ex:
        return None
    
def formatDateOfBirthForOpenAcct(dob:str)->Union[str,None]:
    try:
        input_date = datetime.strptime(dob,"%d%m%Y")
        return input_date.strftime("%Y-%m-%d")
    except Exception as ex:
        return None

def parseVerifymeDateOfBirth(dob:str)->Union[str,None]:
    try:
        input_date = datetime.strptime(dob,"%d-%m-%Y")
        return input_date.strftime("%Y%m%d")
    except Exception as ex:
        return None
def generateCheckDigit(serialNumber: str, bankCode: str) -> int:
    seed = "373373373373"
    serialNumLength = 9

    # Validate lengths
    if len(bankCode) != 3:
        raise ValueError("Bank code must be 3 digits")
    if len(serialNumber) > serialNumLength:
        raise ValueError("Serial number must be at most 9 digits")

    # Zero pad serial number to 9 digits
    padded_serial = serialNumber.zfill(serialNumLength)

    # Concatenate bank code and padded serial number
    cipher = bankCode + padded_serial

    if len(cipher) != len(seed):
        raise ValueError("Combined length of bankCode and serialNumber must be 12 digits")

    total = 0
    for idx, x in enumerate(cipher):
        logger.info(f"Digit: {x}, Seed: {seed[idx]}")
        total += int(x) * int(seed[idx])

    remainder = total % 10
    checkDigit = 10 - remainder
    return 0 if checkDigit == 10 else checkDigit

def formXml(setting: Setting, phone: str, content: str):
    root = ET.Element("operation", {"type": "submit"})
    account = ET.SubElement(
        root,
        "account",
        {"username": setting.vanso_username, "password": setting.vanso_password},
    )
    submitRequest = ET.SubElement(root, "submitRequest")
    deliveryReport = ET.SubElement(submitRequest, "deliveryReport")
    deliveryReport.text = "true"
    sourceAddress = ET.SubElement(submitRequest, "sourceAddress", {"type": "network"})
    sourceAddress.text = setting.senderid
    destinationAddress = ET.SubElement(
        submitRequest, "destinationAddress", {"type": "international"}
    )
    destinationAddress.text = f"+{formatPhone(phone)}"
    text = ET.SubElement(submitRequest, "text", {"encoding": "ISO-8859-1"})
    text.text = stringToHex(content)
    xml = ET.tostring(root, xml_declaration=True, encoding="iso-8859-1")
    logger.info(xml)
    return xml


def stringToHex(string):
    st = ""
    for char in string:
        d = bytearray(char, "ISO-8859-1")
        st = st + hex(ord(d))[2:]
    logger.info(st)
    return st


def create_access_token(setting: Setting, credentials: dict, exp:Union[int,None]=20):
    encoded_credentials = credentials.copy()

    expire = datetime.now() + timedelta(
        hours=setting.access_token_expire_minutes
    )
    if exp:
        expire = datetime.now() + timedelta(minutes=exp)
    encoded_credentials.update({"exp": expire})
    encoded_jwt = jwt.encode(
        encoded_credentials, setting.secret_key, algorithm=setting.algorithm
    )
    return [encoded_jwt,str(exp*60)]

# Hash a password using bcrypt
def get_password_hash(password):
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password


# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password, hashed_password):
    logger.info(plain_password)
    logger.info(hashed_password.encode("utf-8"))
    password_byte_enc = plain_password.encode("utf-8")
    return bcrypt.checkpw(
        password=password_byte_enc, hashed_password=hashed_password.encode("utf-8")
    )
def convert_thousand_separator_to_str(number_str):
    # Set the locale to the user's default locale
    locale.setlocale(locale.LC_ALL, '')

    # Convert the string to a float
    number = float(locale.atof(number_str))

    # Convert the float back to a string with the thousand separator
    return locale.format_string("%d", number, grouping=True)

def getKoboValue(amount:str):
    amount = amount.replace(',', '')
    kobo = int(float(amount) * 100)
    return kobo

def decodeId(id:str):
    decoded_bytes = base64.b64decode(id)
    return decoded_bytes.decode('utf-8')

@lru_cache()
def get_setting():
    return AppSetting()


class UnicornException(Exception):
    def __init__(self, status: int, error: dict):
        self.status = status
        self.name = error
