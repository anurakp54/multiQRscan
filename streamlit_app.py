import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pyodbc as pyodbc
import streamlit as st
from PIL import Image
import zbarlight
import os
from datetime import datetime

#--- USER AUTHENTICATION --

names = ["CKST", "admin"]
usernames = ["CKST", "admin"]


file_path = Path(__file__).parent/"hashed_pw.pkl"
print(file_path)

with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,"Scanner", "ttyyuu", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("login","sidebar")

if authentication_status == False:
    st.error("Username/Password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status == True:
    authenticator.logout("Logout","sidebar")

    credential = st.secrets["anurak"]
    connection_string = "DefaultEndpointsProtocol=https;AccountName=anurak;AccountKey=NgAAeqBVEbEor+R3cyNihGnWmHDr6UEaO4" \
                        "+o26TTwJm2k/qx9pgHAgq3zGfa7a6EcOkVRyMiwlIE+AStiZxLEw==;EndpointSuffix=core.windows.net "


    st.title('Upload QR into Database')
    temp_file = st.file_uploader("1. Upload picture in PNG or JPEG format")
    if st.button("Save to Cache"):
        with open(Path(__file__).parent/"data"/"temp_file", "wb") as file_handle:
            file_handle.write(temp_file.read())

    try:
        with open(Path(__file__).parent/"data"/"temp_file", 'rb') as image_file:
            image = Image.open(image_file)
            image.load()
            os.remove(Path(__file__).parent/"data"/"temp_file")
            codes = zbarlight.scan_codes(['qrcode'], image)

        server = 'tcp:dcdbserverdev.database.windows.net,1433'
        _database = 'dccr_db'
        username = 'jakkrapan'
        password = st.secrets["dido"]

        driver = '{ODBC Driver 17 for SQL Server}'
        err = []
        for code in codes:
            try:
                st.write('QR codes: %s' % code)
                code = str(code, 'utf-8')
                dwgrev = code.split("/")[-1]
                rev = dwgrev[-2:]
                dwg = dwgrev[:-2]
                cnxn = pyodbc.connect(
                    'DRIVER=' + driver + ';PORT=1433;SERVER=' + server + ';DATABASE=' + _database + '; UID=' + username + ';PWD=' + password + ';Encrypt=yes;TrustServerCertificate=no')
                cursor = cnxn.cursor()
                cursor.execute("insert into documents(doc_num, revision, created) values (?,?,?)",
                               dwg, rev, datetime.now())
                cnxn.commit()
                st.success('The data was pushed to the database!')

            except:
                err.append(f'This {code} can not be uploaded.')

        with open('error.txt', 'w') as f:
            #lines = f.readlines()
            #lines = [line.rstrip() for line in lines]
            if not err:
                pass
            else:
                f.write('\n')
                f.write('error is found on %s' % err)

    except:
        pass
