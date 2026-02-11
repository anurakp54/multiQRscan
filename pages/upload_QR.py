import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import pyodbc as pyodbc
import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import os
from datetime import datetime


def app():

    st.title('Upload QR into Database')
    temp_file = st.file_uploader("1. Upload picture in PNG or JPEG format", key="upload_QR_page")
    if temp_file is not None:

        if st.button("Save to Cache"):
                with open(Path(__file__).parent / "data" / "temp_file", "wb") as file_handle:
                    file_handle.write(temp_file.read())

        try:
            with open(Path(__file__).parent / "data" / "temp_file", 'rb') as image_file:
                image = Image.open(image_file)
                image.load()
                os.remove(Path(__file__).parent / "data" / "temp_file")
                decoded_objects = decode(image)
                codes = [obj.data for obj in decoded_objects]

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
                    st.success('Error!')
                    err.append(f'This {code} can not be uploaded.')

            with open('error.txt', 'w') as f:
                # lines = f.readlines()
                # lines = [line.rstrip() for line in lines]
                if not err:
                    pass
                else:
                    f.write('\n')
                    f.write('error is found on %s' % err)

        except:
            pass

# CRITICAL FIX: Prevent execution on import
if __name__ == "__main__":
    app()