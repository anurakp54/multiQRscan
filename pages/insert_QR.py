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


def app():
    st.title('Insert QR Code')

    workdir = 'data/'
    err = []  # Initialized correctly now

    # 1. Clear old data at start of new run
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)

    files = st.file_uploader("1. Upload Drawing File", accept_multiple_files=True, key="insert_QR_page")

    pdf_path = None
    df = None

    if files:
        for file in files:
            ext = file.name.split(".")[-1].lower()
            if ext == 'pdf':
                pdf_path = os.path.join(workdir, 'pdf_dwg.pdf')
                with open(pdf_path, 'wb') as f:
                    f.write(file.getvalue())
            elif ext in ['xlsx', 'xls']:
                excel_path = os.path.join(workdir, file.name)
                with open(excel_path, 'wb') as f:
                    f.write(file.getvalue())
                df = pd.read_excel(excel_path)

    if pdf_path and df is not None:
        try:
            file_handle = fitz.open(pdf_path)
            num_pages = file_handle.page_count

            # Setup Database Connection ONCE if needed
            register_db = st.sidebar.checkbox("Register to Server?", value=False)
            cnxn = None
            if register_db:
                # Use a single connection for the whole session
                cnxn = pyodbc.connect(
                    'DRIVER=' + driver + ';PORT=1433;SERVER=' + server + ';DATABASE=' + _database + '; UID=' + username + ';PWD=' + password + ';Encrypt=yes;TrustServerCertificate=no')
                cursor = cnxn.cursor()

            with st.spinner('Processing drawings...'):
                for page in range(num_pages):
                    if page >= len(df):
                        break

                    # --- DATA HANDLING ---
                    # Use the data directly from Excel for the DB
                    raw_data = str(df.iloc[page]['Dwg'])
                    rev = raw_data[-2:]
                    dwg = raw_data[:-2]

                    # --- QR INSERTION ---
                    qr_url = f'https://docvalidation.azurewebsites.net/goodforconstruction/{raw_data}'
                    img_qr = qrcode.make(qr_url)
                    temp_qr = 'temp_qr.png'
                    img_qr.save(temp_qr)

                    current_page = file_handle[page]
                    a, b, c, d = current_page.rect

                    if current_page.rotation == 270:
                        image_rectangle = fitz.Rect(d - 70, c - 70, d - 30, c - 30)
                    elif current_page.rotation == 0:
                        image_rectangle = fitz.Rect(c - 70, 30, c - 30, 70)
                    else:
                        image_rectangle = fitz.Rect(d - 70, c - 70, d - 30, c - 30)

                    current_page.insert_image(image_rectangle, filename=temp_qr)

                    # Save individual page
                    out_pdf_name = os.path.join(workdir, f"{raw_data}.pdf")
                    new_pdf = fitz.open()
                    new_pdf.insert_pdf(file_handle, from_page=page, to_page=page)
                    new_pdf.save(out_pdf_name)
                    new_pdf.close()

                    # --- DATABASE UPLOAD (Happens here now!) ---

                    if register_db and cnxn:
                        try:
                            cursor.execute(
                                "INSERT INTO documents(doc_num, revision, created) VALUES (?,?,?)",
                                dwg, rev, datetime.now())
                            cnxn.commit()
                            st.write(f"✅ {raw_data} Registered")
                        except Exception as e:
                            st.write(dwg + rev + ' are NOT successfully uploaded!')
                            err.append(f"DB Error on {raw_data}: {str(e)}")

            # Cleanup
            file_handle.close()
            if os.path.exists(pdf_path): os.remove(pdf_path)
            if os.path.exists('temp_qr.png'): os.remove('temp_qr.png')
            if cnxn: cnxn.close()

            # --- ZIP AND DOWNLOAD ---
            # Zip the contents of 'data/' into a file located in the root directory
            zip_base_name = 'drawings_output'
            shutil.make_archive(zip_base_name, 'zip', workdir)

            with open(f"{zip_base_name}.zip", 'rb') as z:
                st.download_button("Download All PDFs", data=z, file_name="QR_Drawings.zip")

            if err:
                st.warning(f"Uploaded with {len(err)} database errors.")
                with st.expander("Show Errors"):
                    st.write(err)

        except Exception as e:
            st.error(f"Critical Error: {e}")


# Prevent auto-run on import
if __name__ == "__main__":
    app()