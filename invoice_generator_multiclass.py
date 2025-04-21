import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Google Sheets setup using Streamlit secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Groundswell-Business").worksheet("invoices")

# UI
st.title("Invoice Generator + Income Tracker (Multi-Class)")

st.header("Create New Invoice")
student = st.text_input("Student Name")

selected_classes = st.multiselect("Select Classes", [
    "Junior Ballet", "Intermediate Ballet",
    "Junior Contemporary", "Intermediate Contemporary",
    "Junior Jazz", "Advanced Jazz",
    "Junior House & Hip Hop", "Advanced House & Hip Hop",
    "Junior Waacking & Locking", "Advanced Waacking & Locking",
    "Tap Class", "Commercial", "Private"
])

age_group = st.selectbox("Age Group", ["Mini (3–5)", "Junior (6-12)", "Teen (13-16)", "Adult"])

# Price chart
price_chart = {
    "Junior Ballet": {"Mini (3–5)": 5, "Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Intermediate Ballet": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Junior Contemporary": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Intermediate Contemporary": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Junior Jazz": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Advanced Jazz": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Junior House & Hip Hop": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Advanced House & Hip Hop": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Junior Waacking & Locking": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Advanced Waacking & Locking": {"Junior (6-12)": 6.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Tap Class": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Commercial": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Private": {"All": 20}
}

# Calculate rates for selected classes
rates = []
for cls in selected_classes:
    if cls == "Private":
        rate = price_chart["Private"]["All"]
    else:
        rate = price_chart.get(cls, {}).get(age_group, 0)
    rates.append((cls, rate))

# Display rates
st.subheader("Class Rates:")
for cls, rate in rates:
    st.write(f"{cls}: £{rate}")

# Allow optional manual override
manual_override = st.checkbox("Override all rates with a custom value?")
if manual_override:
    rate = st.number_input("Enter custom rate for all classes", min_value=0.0, step=0.5)
    rates = [(cls, rate) for cls, _ in rates]

# Total classes attended
classes_attended = st.number_input("Total number of classes attended (combined)", min_value=0)

# Notes
notes = st.text_area("Notes (optional)")

# Generate invoice
if st.button("Generate Invoice"):
    total_rate = sum(rate for _, rate in rates)
    total = classes_attended * total_rate
    date = datetime.now().strftime("%Y-%m-%d")
    class_names = ", ".join(cls for cls, _ in rates)
    row = [date, student, class_names, classes_attended, total_rate, total, "Unpaid", notes]
    sheet.append_row(row)
    st.success(f"Invoice created for {student} (£{total:.2f})")

    whatsapp_msg = f"Hi {student}, your invoice is ready:\nTotal: £{total:.2f}\nClasses: {class_names} ({classes_attended} at £{total_rate}/class).\nThank you!"
    st.write("**WhatsApp/Email Message:**")
    st.code(whatsapp_msg)
