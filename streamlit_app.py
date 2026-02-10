import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import streamlit as st
from multipage import MultiPage
from pages import insert_QR, read_QR, upload_QR


#--- USER AUTHENTICATION --

names = ["CKST", "admin"]
usernames = ["CKST", "admin"]


file_path = Path(__file__).parent/"hashed_pw.pkl"

with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

# Create credentials dictionary
credentials = {
    "usernames": {}
}

for i, username in enumerate(usernames):
    credentials["usernames"][username] = {
        "name": names[i],
        "password": hashed_passwords[i]
    }

authenticator = stauth.Authenticate(
    credentials,
    "Scanner",
    "ttyyuu",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login", "sidebar")

if authentication_status == False:
    st.error("Username/Password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status == True:

    with st.sidebar:
        st.success('DevOP by Anurak P.')

    authenticator.logout("Logout","sidebar")

    credential = st.secrets["anurak"]
    connection_string = "DefaultEndpointsProtocol=https;AccountName=anurak;AccountKey=NgAAeqBVEbEor+R3cyNihGnWmHDr6UEaO4" \
                        "+o26TTwJm2k/qx9pgHAgq3zGfa7a6EcOkVRyMiwlIE+AStiZxLEw==;EndpointSuffix=core.windows.net "

    app = MultiPage()
    app.add_page("Read QR from Picture", upload_QR.app)
    app.add_page("Insert_QR to PDF", insert_QR.app)
    app.add_page("Read_QR from PDF", read_QR.app)

    app.run()

