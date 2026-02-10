import streamlit as st
import pandas as pd
import fitz
import qrcode
import shutil
import os
import cv2
import pyodbc as pyodbc
from datetime import datetime
from pyzbar.pyzbar import decode
from PIL import Image

# Error message from frontend import *, ModuleNotFoundError: No module named "frontend"
# Solution: pip install PyMuPDF
# then pip uninstall fitz

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

def app():  # Main application for inserting QR Code
    section1 = st.container()

    with st.sidebar:
        st.title('Choose your options')
        option = st.selectbox(
            'Do you want to upload the QR to server',
            ('No', 'Yes'))

        if option == 'Yes':
            st.write('QR Code will be registered to the database')

    with section1:
        try:
            st.title('Insert QR Code')
            files = st.file_uploader("1. Upload Drawing File", accept_multiple_files=True)
            if files is not None:
                for file in files:
                    filename, extension = file.name.split(".")
                    if extension == 'pdf':
                        bytes_data = file.getvalue()
                        with open('data/'+'pdf_dwg.pdf','wb') as f:
                            f.write(bytes_data)
                    else:
                        bytes_data = file.getvalue()
                        with open('data/' + file.name, 'wb') as f:
                            f.write(bytes_data)
                        df = pd.read_excel('data/'+file.name)

            file_handle = fitz.open('data/pdf_dwg.pdf')
            num_pages = file_handle.page_count

            #iterating each page
            for page in range(num_pages):
                data = df.loc[page,'Dwg']
                st.write(data)
                # Encoding data using make() function
                img = qrcode.make('https://docvalidation.azurewebsites.net/goodforconstruction/' + data)
                # Saving as an image file
                img.save('temp_code.png')

                current_page = file_handle[page]
                a, b, c, d = current_page.rect
                #print(current_page.rotation)
                #print(a, b, c, d)

                # image_rectangle = fitz.Rect(50,50,100,100)
                if current_page.rotation == 270:
                    image_rectangle = fitz.Rect(d - 70, c - 70, d - 30, c - 30)

                elif current_page.rotation == 0:
                    image_rectangle = fitz.Rect(c - 70, 30, c - 30, 70)

                else:
                    image_rectangle = fitz.Rect(d - 70, c - 70, d - 30, c - 30)

                img = open('temp_code.png', "rb").read()
                img_xref = 0
                # add the image
                if not current_page.is_wrapped:
                    current_page.wrap_contents()
                current_page.insert_image(image_rectangle, stream=img, xref=img_xref)
                new_pdf = fitz.open()
                new_pdf.insert_pdf(file_handle, from_page=page, to_page=page)
                new_pdf.save('data/'+ df.loc[page, 'Dwg'] + '.pdf')

            os.remove('data/pdf_dwg.pdf')
            workdir = 'data/'
            err = []
            if option =='Yes':
                st.success('System is registering QR to server for GFC')

                for each_path in os.listdir(workdir):
                    if ".pdf" in each_path:
                        # Open PDF file
                        pdf_file = fitz.open(os.path.join(workdir, each_path))

                        # Calculate number of pages in PDF file
                        page_nums = len(pdf_file)
                        images_list = []
                        for page_num in range(page_nums):
                            page_content = pdf_file[page_num]
                            images_list.extend(page_content.get_images())

                        for i, image in enumerate(images_list, start=1):
                            # Extract the image object number
                            xref = image[0]
                            # Extract image
                            base_image = pdf_file.extract_image(xref)
                            # Store image bytes
                            image_bytes = base_image['image']
                            # Store image extension
                            image_ext = base_image['ext']
                            # Generate image file name
                            image_name = 'temp' + str(i) + '.' + image_ext
                            # Save image
                            with open(os.path.join(workdir, image_name), 'wb') as image_file:
                                image_file.write(image_bytes)
                                image_file.close()

                            code = read_qr_code2(workdir + image_name)
                            if code is not None:
                                code = str(code[0], 'utf-8')
                                dwgrev = code.split("/")[-1]
                                rev = dwgrev[-2:]
                                dwg = dwgrev[:-2]
                                st.write(dwg + rev)
                                if len(dwg) > 0:
                                    st.write(dwg + rev + ' are uploading!')
                                    try:
                                        cnxn = pyodbc.connect(
                                            'DRIVER=' + driver + ';PORT=1433;SERVER=' + server + ';DATABASE=' + _database + '; UID=' + username + ';PWD=' + password + ';Encrypt=yes;TrustServerCertificate=no')
                                        cursor = cnxn.cursor()
                                        cursor.execute(
                                            "insert into documents(doc_num, revision, created) values (?,?,?)",
                                            dwg, rev, datetime.now())
                                        cnxn.commit()
                                        st.write(dwg + rev + ' are successfully uploaded!')

                                    except:
                                        st.write(dwg + rev + ' are NOT successfully uploaded!')
                                        err.append(f'This {code} can not be uploaded.')

            shutil.make_archive('dwg_with_qr', 'zip', 'data/')
            st.success("PDF file is being compressed, Click -Download Zip File-")

            with open("dwg_with_qr.zip",'rb') as zipfile:
                btn = st.download_button("Download Zip File", data=zipfile,file_name="drawing_with_QR.zip")

            for f in os.listdir(workdir):
                os.remove(os.path.join(workdir,f))

        except: pass

