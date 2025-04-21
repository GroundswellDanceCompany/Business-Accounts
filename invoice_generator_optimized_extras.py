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
st.title("Invoice Generator with Classes + Extras (Optimized)")

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

age_group = st.selectbox("Age Group", ["Mini (3-5)", "Junior (6-12)", "Teen (13-16)", "Adult"])

# Price chart
price_chart = {
    "Junior Ballet": {"Mini (3-5)": 5, "Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Intermediate Ballet": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Junior Contemporary": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Intermediate Contemporary": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Junior Jazz": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Advanced Jazz": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Junior House & Hip Hop": {"Junior (6-12)": 5.50, "Teen (13-16)": 6},
    "Advanced House & Hip Hop": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Junior Waacking & Locking": {"Junior (6-12)": 5.50, "Teen (13-16)": 6},
    "Advanced Waacking & Locking": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Tap Class": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Commercial": {"Junior (6-12)": 5.50, "Teen (13-16)": 6, "Adult": 6.50},
    "Private": {"All": 20}
}

# Calculate class rates
rates = []
for cls in selected_classes:
    if cls == "Private":
        rate = price_chart["Private"]["All"]
    else:
        rate = price_chart.get(cls, {}).get(age_group, 0)
    rates.append((cls, rate))

st.subheader("Class Rates")
for cls, rate in rates:
    st.write(f"{cls}: £{rate:.2f}")

# Optional override
manual_override = st.checkbox("Override all rates with a custom value?")
if manual_override:
    custom_rate = st.number_input("Enter custom rate", min_value=0.0, step=0.5)
    rates = [(cls, custom_rate) for cls, _ in rates]

classes_attended = st.number_input("Total number of classes attended (combined)", min_value=0)

# Predefined extras
available_extras = [
    "Team Training",
    "Extra Rehearsal",
    "Costume Fee",
    "Workshop Fee",
    "Exam Entry",
    "Competition Fee"
]

# Manage extras using session_state
if "extras" not in st.session_state:
    st.session_state.extras = []

st.subheader("Extras (Predefined Selection)")
with st.form("add_extra_form", clear_on_submit=True):
    extra_name = st.selectbox("Choose Extra Type", available_extras)
    extra_amount = st.number_input("Amount", min_value=0.0, step=0.5)
    submit_extra = st.form_submit_button("Add Extra")
    if submit_extra and extra_name and extra_amount > 0:
        st.session_state.extras.append((extra_name, extra_amount))

if st.session_state.extras:
    st.write("**Added Extras:**")
    for i, (name, amt) in enumerate(st.session_state.extras):
        st.write(f"{i+1}. {name} - Â£{amt:.2f}")

# Notes
notes = st.text_area("Notes (optional)")

# Final calculation and invoice creation
if st.button("Generate Invoice"):
    total_class_rate = sum(rate for _, rate in rates)
    class_total = classes_attended * total_class_rate
    extras_total = sum(amount for _, amount in st.session_state.extras)
    grand_total = class_total + extras_total

    date = datetime.now().strftime("%Y-%m-%d")
    class_names = ", ".join(cls for cls, _ in rates)
    extra_names = ", ".join(f"{name} (£{amount})" for name, amount in st.session_state.extras)

    row = [date, student, class_names + (", " + extra_names if extra_names else ""), classes_attended, total_class_rate, grand_total, "Unpaid", notes]
    sheet.append_row(row)

    st.success(f"Invoice created for {student} (£{grand_total:.2f})")

    whatsapp_msg = f"Hi {student}, your invoice is ready:\nTotal: £{grand_total:.2f}\nClasses: {class_names} ({classes_attended} at £{total_class_rate}/class)"
    if st.session_state.extras:
        whatsapp_msg += f"\nExtras: {extra_names}"
    whatsapp_msg += "\nThank you!"
    st.write("**WhatsApp/Email Message:**")
    st.code(whatsapp_msg)

    # Clear extras for next entry
    st.session_state.extras = []
