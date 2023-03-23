import streamlit as st
import pandas as pd
import fitz
import qrcode
import shutil
import os

# Error massage from frontend import *, ModuleNotFoundError: No module named "frontend"
# Solution: pip install PyMuPDF
# then pip uninstall fitz


def app():  # Main application for inserting QR Code
    section1 = st.container()
    try:
        with section1:
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
            st.success("PDF file is being compressed, Click -Download Zip File-")
            shutil.make_archive('dwg_with_qr','zip','data/')
            with open("dwg_with_qr.zip",'rb') as zipfile:
                btn = st.download_button("Download Zip File", data=zipfile,file_name="drawing_with_QR.zip")

            directory = 'data/'
            for f in os.listdir(directory):
                os.remove(os.path.join(directory,f))

    except: pass