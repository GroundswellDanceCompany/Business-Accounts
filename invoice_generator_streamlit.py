
import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Groundswell-Business").worksheet("invoices")

# UI
st.title("Invoice Generator + Income Tracker")

st.header("Create New Invoice")

student = st.text_input("Student Name")
class_type = st.selectbox("Class Type", ["Junior Ballet", "Intermediate Ballet", "Junior Contemporary", "Intermediate Contemporary', "Junior Jazz", "Advanced Jazz", "Junior House & Hip Hop", "Advanced House & Hip Hop", "Junior Waacking & Locking", "Advanced Waacking & Locking", "Private"])
age_group = st.selectbox("Age Group", ["Mini (3–6)", "Junior (7–12)", "Teen (13-16)", "Adult"])
price_chart = {
    "Ballet": {
        "Mini (3–5)": 5,
        "Junior (7–12)": 5.50,
        "Teen (13-16)": 6,
        "Adult": 6.50
    },
    "Hip Hop": {
        "Mini (3–6)": 6,
        "Junior (7–10)": 7,
        "Teen (11–16)": 9,
        "Adult": 10
    },
    "Contemporary": {
        "Teen (11–16)": 9,
        "Adult": 10
    },
    "Private": {
        "All": 20
    }
}

default_rate = price_chart.get(class_type, {}).get(age_group, 0)
if class_type == "Private":
    default_rate = price_chart["Private"]["All"]

st.subheader(f"Standard Rate: £{default_rate}")
manual_override = st.checkbox("Override rate manually?")
if manual_override:
    rate = st.number_input("Enter custom rate", min_value=0.0, step=0.5)
else:
    rate = default_rate
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
