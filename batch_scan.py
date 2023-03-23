import os
import fitz  # pip install --upgrade pip; pip install --upgrade pymupdf
from tqdm import tqdm  # pip install tqdm
import cv2
from datetime import datetime
import pyodbc as pyodbc
import streamlit as st

#  This scrip will read the QR code from pdf file in data folder.
#  The data will be uploaded to docvalidation server Azure.
#  Several drawings will be read and uploaded one by one to the server.

server = 'tcp:dcdbserverdev.database.windows.net,1433'
_database = 'dccr_db'
username = 'jakkrapan'
password = st.secrets["dido"]
driver = '{ODBC Driver 17 for SQL Server}'

def read_qr_code(filename):

    try:
        img = cv2.imread(filename)
        detect = cv2.QRCodeDetector()
        value, points, straight_qrcode = detect.detectAndDecode(img)
        return value
    except:
        return

workdir = '/Volumes/Extreme 500/PycharmProjects/QRMultiScan/data/'
err =[]
for each_path in os.listdir(workdir):
    if ".pdf" in each_path:
        doc = fitz.Document((os.path.join(workdir, each_path)))

        for i in tqdm(range(len(doc)), desc="pages"):
            for img in tqdm(doc.get_page_images(i), desc="page_images"):
                xref = img[0]
                image = doc.extract_image(xref)
                pix = fitz.Pixmap(doc, xref)
                #pix.save(os.path.join(workdir, "%s_p%s-%s.png" % (each_path[:-4], i, xref)))
                pix.save(os.path.join(workdir,"temp.png"))
                code = read_qr_code(os.path.join(workdir,'temp.png'))
                dwgrev = code.split("/")[-1]
                rev = dwgrev[-2:]
                dwg = dwgrev[:-2]

                if len(dwg) > 0:
                    try:
                        cnxn = pyodbc.connect(
                        'DRIVER=' + driver + ';PORT=1433;SERVER=' + server + ';DATABASE=' + _database + '; UID=' + username + ';PWD=' + password + ';Encrypt=yes;TrustServerCertificate=no')
                        cursor = cnxn.cursor()
                        cursor.execute("insert into documents(doc_num, revision, created) values (?,?,?)",
                                       dwg, rev, datetime.now())
                        cnxn.commit()
                        print(dwg +' are successfully uploaded!')

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