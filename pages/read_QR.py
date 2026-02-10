import os
import fitz  # pip install --upgrade pip; pip install --upgrade pymupdf
from tqdm import tqdm  # pip install tqdm
import cv2
from datetime import datetime
import pyodbc as pyodbc
import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode


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

def read_qr_code2(filename):
    with open(filename, 'rb') as image_file:
        image = Image.open(image_file)
        image.load()

    decoded_objects = decode(image)
    value = [obj.data for obj in decoded_objects]
    #print('QR codes: %s' % codes)
    return value

def app():
    workdir = 'data/'
    for f in os.listdir(workdir):
        os.remove(os.path.join(workdir, f))

    err = []
    with st.sidebar:
        st.title("Scan QR Code and Push to Server")

    section1 = st.container()
    with section1:
        st.title('Upload PDF File for QR Reading and pushing to server')
        xfiles = st.file_uploader("1. Upload Drawing File", accept_multiple_files=True)
        if xfiles is not None:
            for file in xfiles:
                filename, extension = file.name.split(".")
                if extension == 'pdf':
                    bytes_data = file.getvalue()
                    with open('data/' + file.name, 'wb') as f:
                        f.write(bytes_data)
                else:
                    pass

        #file_handle = fitz.open('data/pdf_dwg.pdf')
        #num_pages = file_handle.page_count

        for each_path in os.listdir(workdir):
            if ".pdf" in each_path:
                doc = fitz.Document((os.path.join(workdir, each_path)))

                for i in tqdm(range(len(doc)), desc="pages"):
                    for img in tqdm(doc.get_page_images(i), desc="page_images"):
                        xref = img[0]
                        image = doc.extract_image(xref)
                        pix = fitz.Pixmap(doc, xref)
                        # pix.save(os.path.join(workdir, "%s_p%s-%s.png" % (each_path[:-4], i, xref)))
                        pix.save(os.path.join(workdir, "temp.png"))

                        code = read_qr_code2(os.path.join(workdir, 'temp.png'))
                        if code is not None:
                            code = str(code[0], 'utf-8')
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
                                    st.write(dwg + rev + ' are successfully uploaded!')

                                except:
                                    err.append(f'This {code} can not be uploaded.')

        directory = 'data/'
        for f in os.listdir(directory):
            os.remove(os.path.join(directory, f))

        with open('error.txt', 'w') as f:
            # lines = f.readlines()
            # lines = [line.rstrip() for line in lines]
            if not err:
                pass
            else:
                f.write('\n')
                f.write('error is found on %s' % err)