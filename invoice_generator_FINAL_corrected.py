import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timedelta

# Google Sheets setup using Streamlit secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Groundswell-Business").worksheet("invoices")

# UI
st.title("Monthly Invoice Generator (with Dated Extras)")

st.header("Create New Invoice")
student = st.text_input("Student Name")

# Invoice period
today = date.today()
invoice_start = st.date_input("Invoice Start Date", value=today)
invoice_end = st.date_input("Invoice End Date", value=today + timedelta(weeks=4))

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
    "Commercial": {"Junior (6-12)": 5.50,"Teen (13-16)": 6, "Adult": 6.50},
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
available_extras = {
    "Subscription": [
        "Team Training-GFoundation",
        "Team Training-GSD Youth",
        "Team Training-Jenga",
        "Team Training-Youth Contemporary",
        "Team Training-Youth Jazz",
        "Team Training-Junior Contemporary",
        "Team Training-Junior Jazz"
        
    "Session-Based": [
        "Extra Rehearsal - Competition",
        "Extra Rehearsal - Show",
        "Private Lesson"],
        
    "One-Off": [
        "Costume Fee", 
        "Uniform Fee", 
        "Exam Entry", 
        "Competition Fee"]
}

# Flatten all extras for selection
all_extras = [item for sublist in available_extras.values() for item in sublist]

# Manage structured extras with session_state
if "extras" not in st.session_state:
    st.session_state.extras = []

st.subheader("Extras")
with st.form("add_extra_form", clear_on_submit=True):
    extra_name = st.selectbox("Choose Extra", all_extras)
    extra_type = None
    for typ, items in available_extras.items():
        if extra_name in items:
            extra_type = typ
            break

    extra_amount = st.number_input("Amount", min_value=0.0, step=0.5)
    extra_date = None
    if extra_type == "Session-Based":
        extra_date = st.date_input("Date of Session", value=date.today())

    submit_extra = st.form_submit_button("Add Extra")

    if submit_extra and extra_name and extra_amount > 0:
        st.session_state.extras.append({
            "name": extra_name,
            "type": extra_type,
            "amount": extra_amount,
            "date": str(extra_date) if extra_date else ""
        })

# Display added extras
if st.session_state.extras:
    st.write("**Added Extras:**")
    for i, ex in enumerate(st.session_state.extras):
        desc = f"{ex['name']} ({ex['type']})"
        if ex['type'] == "Session-Based" and ex['date']:
            desc += f" on {ex['date']}"
        st.write(f"{i+1}. {desc}: Â£{ex['amount']:.2f}")

# Notes
notes = st.text_area("Notes (optional)")

# Final calculation and invoice creation
if st.button("Generate Invoice"):
    total_class_rate = sum(rate for _, rate in rates)
    class_total = classes_attended * total_class_rate
    extras_total = sum(extra["amount"] for extra in st.session_state.extras)
    grand_total = class_total + extras_total

    invoice_period = f"{invoice_start} to {invoice_end}"
    date_created = datetime.now().strftime("%Y-%m-%d")
    class_names = ", ".join(cls for cls, _ in rates)
    extra_names = ", ".join(
    f"{ex['name']} ({ex['type']}" +
    (f" on {ex['date']}" if ex['type'] == "Session-Based" and ex['date'] else "") +
    f"): £{ex['amount']:.2f}"
    for ex in st.session_state.extras
)

    row = [date_created, invoice_period, student, class_names, classes_attended, total_class_rate, extra_names, extras_total, grand_total, "Unpaid", notes]
    sheet.append_row(row)

    st.success(f"Invoice created for {student} (£{grand_total:.2f})")

    whatsapp_msg = (
        f"Hi {student}, your invoice for the period {invoice_period} is ready.\n"
        f"Total: £{grand_total:.2f}\n"
        f"Classes: {class_names} ({classes_attended} at £{total_class_rate}/class)"
    )
    if st.session_state.extras:
        whatsapp_msg += f"\nExtras: {extra_names}"
    whatsapp_msg += "\nThank you!"
    st.write("**WhatsApp/Email Message:**")
    st.code(whatsapp_msg)

    # Clear extras after invoice creation
    st.session_state.extras = []
