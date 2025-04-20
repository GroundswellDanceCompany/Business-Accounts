
import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Dance_Students_Invoice").worksheet("invoices")

# UI
st.title("Invoice Generator + Income Tracker")

st.header("Create New Invoice")

student = st.text_input("Student Name")
class_type = st.selectbox("Class Type", ["Ballet", "Hip Hop", "Contemporary", "Private"])
classes_attended = st.number_input("Classes Attended", min_value=0)
rate = st.number_input("Rate per Class", value=15.0)
notes = st.text_area("Notes (optional)")

if st.button("Generate Invoice"):
    total = classes_attended * rate
    date = datetime.now().strftime("%Y-%m-%d")
    row = [date, student, class_type, classes_attended, rate, total, "Unpaid", notes]
    sheet.append_row(row)
    st.success(f"Invoice created for {student} (${total:.2f})")
    
    whatsapp_msg = f"Hi {student}, your invoice is ready:\nTotal: ${total:.2f}\nClasses: {class_type} ({classes_attended} classes @ ${rate}/class)\nThank you!"
    st.write("**WhatsApp/Email Message:**")
    st.code(whatsapp_msg)
