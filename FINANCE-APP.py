import streamlit as st

st.set_page_config(page_title="Dance School OS", layout="wide")

tabs = ["Invoice Generator", "Student Manager", "Registers", "Accounts Package", "Invoices Dashboard", "Revenue Forecast", "Ask AI", "Manager Dashboard"]
selection = st.sidebar.radio("Choose View", tabs)

if selection == "Invoice Generator":
    import json
    import streamlit as st
    import gspread
    import pandas as pd
    from oauth2client.service_account import ServiceAccountCredentials
    from datetime import datetime, date, timedelta
    import os
    
    from docx import Document

import os
from datetime import datetime
from docx import Document

def generate_invoice_doc(student_name, date_from, date_to, class_list, extras, total):
    # 1. Build target folder
    folder = os.path.join(os.getcwd(), "Groundswell Dance Company")
    os.makedirs(folder, exist_ok=True)

    # 2. Clean file name and full save path
    safe_name = student_name.replace(" ", "_")
    filename = f"{safe_name}_{date_from}_to_{date_to}.docx"
    save_path = os.path.join(folder, filename)

    # 3. Load template and fill it
    template_path = "invoice_template.docx"
    doc = Document(template_path)

    for paragraph in doc.paragraphs:
        if "{{student_name}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{student_name}}", student_name)
        if "{{date_from}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{date_from}}", date_from)
        if "{{date_to}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{date_to}}", date_to)
        if "{{class_list}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{class_list}}", "\n".join(class_list))
        if "{{extras}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{extras}}", "\n".join(extras))
        if "{{total}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{total}}", f"{total:.2f}")

    doc.save(save_path)
    return save_path

def show_followup(label, callback, *args, **kwargs):
    st.markdown(f"**Next step:**")
    if st.button(label):
        callback(*args, **kwargs)

def show_student_invoices(student_name):
    result = df[df["Student"].str.contains(student_name, case=False)]
    st.dataframe(result)

def show_invoices_by_month(month_period):
    filtered = df[df["Date created"].dt.to_period("M") == month_period]
    st.markdown(f"### Invoices for {month_period}")
    st.dataframe(filtered)

def show_reminder_email(student_name):
    result = df[(df["Student"].str.contains(student_name, case=False)) & (df["Status"] == "Unpaid")]
    amount = result["Grand total"].sum()

    if amount > 0:
        email_text = send_reminder_email(student_name, amount)
        st.text_area(f"Reminder email for {student_name}", email_text, height=150)

def show_high_value_invoices(threshold=100):
    filtered = df[df["Grand total"] >= threshold]
    st.markdown(f"### Invoices Over £{threshold}")
    st.dataframe(filtered)
    
    # Google Sheets setup using Streamlit secrets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Groundswell-Business").worksheet("invoices")

if selection == "Invoice Generator":

    st.title("Monthly Invoice Generator")
    
    st.header("Create New Invoice")
    student = st.text_input("Student Name")
    
    # Invoice period
    today = date.today()
    invoice_start = st.date_input("Invoice Start Date", value=today)
    invoice_end = st.date_input("Invoice End Date", value=today + timedelta(weeks=4))
    invoice_label = st.text_input("Custom Invoice Label (e.g. Maya - April 2025)", value=f"{student} - {invoice_start.strftime('%b %Y')}")
    
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
        "Private": {"All": 30}
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
        ],   
        "Session-Based": [
            "Extra Rehearsal - Competition",
            "Extra Rehearsal - Show",
            "Private Lesson",
            "Open House Class"
        ],    
        "One-Off": [
            "Costume Fee", 
            "Uniform Fee", 
            "Exam Entry", 
            "Competition Fee"
        ]
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
            st.write(f"{i+1}. {desc}: £{ex['amount']:.2f}")
    
    # Notes
    notes = st.text_area("Notes (optional)")
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Groundswell-Business").worksheet("invoices")

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
        invoice_label = f"{student} - {invoice_start.strftime('%b %Y')}"

        row = [
            date_created, invoice_period, student, class_names, classes_attended,
            total_class_rate, extra_names, extras_total, grand_total,
            "Unpaid", notes, invoice_label
        ]
        sheet.append_row(row)

        # Word doc generation
        invoice_path = generate_invoice_doc(
            student_name=student,
            date_from=invoice_start.strftime("%Y-%m-%d"),
            date_to=invoice_end.strftime("%Y-%m-%d"),
            class_list=[f"{cls}: £{rate:.2f}" for cls, rate in rates],
            extras=[f"{ex['name']} – £{ex['amount']:.2f}" for ex in st.session_state.extras],
            total=grand_total
        )

        with open(invoice_path, "rb") as file:
            st.download_button(
                label="Download Invoice (Word)",
                data=file,
                file_name=os.path.basename(invoice_path),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        st.success(f"Invoice created for {student} (£{grand_total:.2f})")
        st.session_state.extras = []
        
elif selection == "Student Manager":
    import streamlit as st
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    from datetime import date

    # Handle refresh after student/class update
    if st.session_state.get("refresh_students"):
        st.session_state.refresh_students = False
        st.rerun()
    if st.session_state.get("refresh_enrollment"):
        st.session_state.refresh_enrollment = False
        st.rerun()

    st.header("Student & Class Management")

    # Google Sheets setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    students_sheet = client.open("Groundswell-Business").worksheet("students")
    classes_sheet = client.open("Groundswell-Business").worksheet("class_enrollments")

    # Load current student data
    students_data = students_sheet.get_all_records()
    student_names = [s.get("Name") for s in students_data if s.get("Name")]

    from datetime import date

    def calculate_age_group(dob):
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age <= 5:
            return "Mini (3-5)"
        elif 6 <= age <= 12:
            return "Junior (6-12)"
        elif 13 <= age <= 16:
            return "Teen (13-16)"
        else:
            return "Adult"

    # --------------------------
    # Add / Edit Student Form
    # --------------------------
    st.subheader("Add / Edit Student")

    with st.form("student_form", clear_on_submit=True):
        name = st.text_input("Name")
        dob = st.date_input(
            "Date of Birth",
            value=date(2010, 1, 1),
            min_value=date(2000, 1, 1),
            max_value=date.today()
        )
        contact = st.text_input("Contact")
        notes = st.text_area("Notes")
        submit = st.form_submit_button("Save Student")

        if submit and name:
            age_group = calculate_age_group(dob)
            students_sheet.append_row([name, str(dob), age_group, contact, notes])
            st.success(f"Student '{name}' added successfully!")
            st.markdown(f"**Assigned Age Group:** {age_group}")

    st.info("If you just added a student, refresh to update the list below.")
    if st.button("Refresh Student List"):
        st.session_state.refresh_students = True
        st.rerun()
            
    st.divider()
    st.subheader("Assign Student to Class")

    with st.form("class_assign_form", clear_on_submit=True):
        student = st.selectbox("Select Student", options=student_names)
        selected_classes = st.multiselect("Select Class(es)", [
            "Junior Ballet", "Intermediate Ballet",
            "Junior Contemporary", "Intermediate Contemporary",
            "Junior Jazz", "Advanced Jazz",
            "Junior House & Hip Hop", "Advanced House & Hip Hop",
            "Junior Waacking & Locking", "Advanced Waacking & Locking",
            "Tap Class", "Commercial", "Private"
        ])
        enroll = st.form_submit_button("Assign to Class")

        if enroll and student and selected_classes:
            students_data = students_sheet.get_all_records()  # Ensure it's up to date
            student_info = next((s for s in students_data if s["Name"] == student), None)
            age_group = student_info["Age group"] if student_info else "Unknown"

            for cls in selected_classes:
                classes_sheet.append_row([student, cls, age_group, "Enrolled"])
            st.success(f"{student} assigned to: {', '.join(selected_classes)}")

    
    st.divider()
    st.subheader("Class Rosters")
    try:
        roster_data = classes_sheet.get_all_records()
        if roster_data and isinstance(roster_data, list):
            df_roster = pd.DataFrame(roster_data)
            if "Class" in df_roster.columns and "Student" in df_roster.columns:
                available_classes = sorted(df_roster["Class"].dropna().unique().tolist())
                selected_class = st.selectbox("Select a class to view roster", available_classes)
                class_roster = df_roster[df_roster["Class"] == selected_class]
                if not class_roster.empty:
                    st.write(f"### Students Enrolled in: {selected_class}")
                    st.dataframe(class_roster[["Student", "Age group", "Status"]])
                    csv_data = class_roster.to_csv(index=False)
                    st.download_button("Download Roster as CSV", csv_data, file_name=f"{selected_class}_roster.csv", mime="text/csv")
                else:
                    st.info("No students found for this class.")
            else:
                st.warning("Sheet is missing 'Class' or 'Student' columns.")
        else:
            st.info("No enrollment data available.")
    except Exception as e:
        st.error(f"Error loading roster: {e}")

elif selection == "Registers":
    import streamlit as st
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    from datetime import date
    
    st.header("Attendance Register")

    # Connect to Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    classes_sheet = client.open("Groundswell-Business").worksheet("class_enrollments")
    attendance_sheet = client.open("Groundswell-Business").worksheet("attendance_records")

    # Select class and date
    class_list = sorted(list(set(row["Class"] for row in classes_sheet.get_all_records() if row["Class"])))
    selected_class = st.selectbox("Select Class", class_list)
    selected_date = st.date_input("Date", value=date.today())

    # Load students enrolled in that class
    enrolled_data = classes_sheet.get_all_records()
    enrolled_students = [row for row in enrolled_data if row["Class"] == selected_class]

    if not enrolled_students:
        st.info("No students are enrolled in this class.")
    else:
        st.subheader(f"Mark Attendance for: {selected_class}")
        attendance = {}

        for student in enrolled_students:
            col1, col2 = st.columns([3, 2])
            with col1:
                present = st.checkbox(f"{student['Student']}", key=student['Student'])
            with col2:
                note = st.text_input(f"Notes for {student['Student']}", key=f"{student['Student']}_note")
            attendance[student["Student"]] = {"present": present, "note": note}

        if st.button("Submit Attendance"):
            for student_name, data in attendance.items():
                attendance_sheet.append_row([
                    str(selected_date),
                    selected_class,
                    student_name,
                    "Present" if data["present"] else "Absent",
                    data["note"]
                ])
            st.success("Attendance saved successfully!")

elif selection == "Accounts Package":
    import pandas as pd
    import calendar
    from datetime import datetime
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    st.header("Accounts Package")

    # Google Sheets Setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    expenses_sheet = client.open("Groundswell-Business").worksheet("expenses")

    def load_expenses(sheet):
        data = sheet.get_all_records(expected_headers=["Date", "Category", "Description", "Amount", "Receipt URL"])
        df = pd.DataFrame(data)
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
            df["Month"] = df["Date"].dt.strftime("%B")
            df["Year"] = df["Date"].dt.year.astype("Int64")
            df["MonthNum"] = df["Date"].dt.month
        return df
    # Track state for manual refresh
    if "trigger_reload" not in st.session_state:
        st.session_state["trigger_reload"] = False

    tab1, tab2, tab3 = st.tabs(["Add Expense", "Overview", "Expense Records"])

    # Tab 1: Add Expense
    with tab1:
        expenses = load_expenses(expenses_sheet)
        st.subheader("Upload New Expense")
        with st.form("upload_expense_form", clear_on_submit=True):
            expense_date = st.date_input("Date", value=datetime.today())
            category = st.selectbox("Category", ["Costumes", "Studio Rent", "Music Subscriptions", "Travel", "Admin", "Other"])
            description = st.text_input("Description")
            amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)
            receipt_url = st.text_input("Receipt URL (optional)")
            submitted = st.form_submit_button("Add Expense")

            if submitted:
                expenses_sheet.append_row([
                    expense_date.strftime("%Y-%m-%d"),
                    category,
                    description,
                    f"{amount:.2f}",
                    receipt_url
                ])
                st.success("Expense added successfully.")
                st.session_state["refresh_expenses"] = True

    # Refresh button logic
    st.divider()
    if st.session_state["trigger_reload"]:
        if st.button("Refresh Data Now"):
            st.session_state["trigger_reload"] = False

    # Load and process data if not waiting for refresh
    if not st.session_state["trigger_reload"]:
        raw_data = expenses_sheet.get_all_values()

        if not raw_data or len(raw_data) < 2:
            st.warning("No valid expense data found.")
            expenses = pd.DataFrame(columns=["Date", "Category", "Description", "Amount", "Receipt URL", "Month", "Year", "MonthNum"])
        else:
            headers = [h.strip() for h in raw_data[0]]
            rows = [row for row in raw_data[1:] if any(cell.strip() for cell in row)]
            cleaned_rows = [row + [""] * (len(headers) - len(row)) for row in rows]
            expenses = pd.DataFrame(cleaned_rows, columns=headers)

            # Standardise and parse
            expenses["Date"] = pd.to_datetime(expenses["Date"], errors="coerce")
            expenses["Amount"] = pd.to_numeric(expenses["Amount"], errors="coerce")
            expenses["Month"] = expenses["Date"].dt.strftime("%B")
            expenses["Year"] = expenses["Date"].dt.year.astype("Int64")
            expenses["MonthNum"] = expenses["Date"].dt.month

        # Tab 2: Overview
        with tab2:
            expenses = load_expenses(expenses_sheet)
            st.subheader("Monthly Profit & Loss Overview")
            if not expenses.empty:
                monthly_summary = (
                    expenses.groupby(["Year", "MonthNum", "Month"])
                    .sum(numeric_only=True)["Amount"]
                    .reset_index()
                    .sort_values(["Year", "MonthNum"])
                )
                monthly_summary["Label"] = monthly_summary["Month"] + " " + monthly_summary["Year"].astype(str)
                st.bar_chart(monthly_summary.set_index("Label")["Amount"])
                st.metric("Total Expenses (YTD)", f"£{expenses['Amount'].sum():.2f}")
            else:
                st.info("No data available.")

        # Tab 3: Expense Records
        with tab3:
            expenses = load_expenses(expenses_sheet)
            st.subheader("Filter and Export Expense Records")
            if not expenses.empty:
                years = sorted(expenses["Year"].dropna().unique(), reverse=True)
                months = list(calendar.month_name)[1:]
                selected_year = st.selectbox("Year", years, index=0)
                selected_month = st.selectbox("Month", months)

                month_num = months.index(selected_month) + 1
                filtered = expenses[
                    (expenses["Year"] == selected_year) &
                    (expenses["MonthNum"] == month_num)
                ]

                category_filter = st.multiselect("Filter by Category", expenses["Category"].unique(), default=expenses["Category"].unique())
                filtered = filtered[filtered["Category"].isin(category_filter)]

                st.dataframe(filtered[["Date", "Category", "Description", "Amount", "Receipt URL"]])
                st.download_button("Download Filtered as CSV", filtered.to_csv(index=False), "filtered_expenses.csv")
            else:
                st.info("No expenses to display.")
    else:
        st.warning("New expense added. Click 'Refresh Data Now' to update the charts.")

elif selection == "Invoices Dashboard":
    import json
    import streamlit as st
    import gspread
    import pandas as pd
    from oauth2client.service_account import ServiceAccountCredentials
    from datetime import datetime
    
    # Google Sheets setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Groundswell-Business").worksheet("invoices")
    
    # Load data

    def load_data():
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    
    df = load_data()
    
    # Parse data with correct column names
    df["Date created"] = pd.to_datetime(df["Date created"], errors="coerce")
    df["Grand total"] = pd.to_numeric(df["Grand total"], errors="coerce")
    df["Status"] = df["Status"].fillna("Unpaid")
    
    st.title("Dance School Invoice Dashboard")
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Filter by custom Invoice Label
        if "Invoice label" in df.columns:
            labels = df["Invoice label"].dropna().unique().tolist()
            selected_labels = st.multiselect("Invoice Label", options=labels, default=labels)
        else:
            selected_labels = df["Student"].unique().tolist()  # fallback

        selected_status = st.multiselect("Payment Status", options=df["Status"].unique(), default=df["Status"].unique())
        min_date = df["Date created"].min()
        max_date = df["Date created"].max()
        selected_range = st.date_input("Date Range", value=(min_date, max_date))
    
    # Apply filters
    filtered_df = df[
    (df["Status"].isin(selected_status)) &
    (df["Invoice label"].isin(selected_labels)) &
    (df["Date created"] >= pd.to_datetime(selected_range[0])) &
    (df["Date created"] <= pd.to_datetime(selected_range[1]))
]
    
    # KPI summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Invoiced", f"£{filtered_df['Grand total'].sum():.2f}")
    col2.metric("Paid", f"£{filtered_df[filtered_df['Status'] == 'Paid']['Grand total'].sum():.2f}")
    col3.metric("Unpaid", f"£{filtered_df[filtered_df['Status'] == 'Unpaid']['Grand total'].sum():.2f}")
    
    # Totals by student
    st.subheader("Invoice Summary by Label")
    st.dataframe(filtered_df[["Invoice label", "Student", "Grand total", "Status"]])
    
    # Monthly trend
    st.subheader("Monthly Invoice Trend")
    monthly = filtered_df.groupby(filtered_df["Date created"].dt.to_period("M"))["Grand total"].sum().reset_index()
    monthly["Month"] = monthly["Date created"].astype(str)
    st.line_chart(monthly.set_index("Month"))
    
    # Revenue by Student breakdown
    st.subheader("Revenue by Student")
    student_totals = filtered_df.groupby("Student")["Grand total"].sum().sort_values(ascending=False)
    st.bar_chart(student_totals)
    
    # Full data view
    with st.expander("See Filtered Invoice Data"):
        st.dataframe(filtered_df)

    # Add 'Mark as Paid' functionality
    st.subheader("Mark Invoices as Paid")

    unpaid_invoices = df[df["Status"] != "Paid"]
    if not unpaid_invoices.empty:
        selected_to_mark = st.multiselect(
            "Select Invoice Labels to Mark as Paid",
            options=unpaid_invoices["Invoice label"].dropna().unique().tolist()
        )

        if st.button("Mark Selected as Paid"):
            worksheet = sheet
            all_data = worksheet.get_all_values()
            headers = all_data[0]
            label_index = headers.index("Invoice label")
            status_index = headers.index("Status")
            
            updated = 0
            
            for i, row in enumerate(all_data[1:], start=2):
                label = row[label_index].strip()
                if label in [s.strip() for s in selected_to_mark]:
                    worksheet.update_cell(i, status_index + 1, "Paid")
                    updated += 1

            if updated:
                st.success(f"{updated} invoice(s) marked as Paid.")
                st.info("Marked as Paid. Please refresh manually or use the button below.")
                if st.button("Refresh Now"):
                    st.experimental_rerun()
                
            else:
                st.warning("No matching rows were found to update.")

    else:
        st.info("No unpaid invoices found.")

    # CSV export
    st.download_button("Download Filtered Data as CSV", data=filtered_df.to_csv(index=False), file_name="invoices_filtered.csv", mime="text/csv")


elif selection == "Revenue Forecast":
    import streamlit as st
    import pandas as pd
    import numpy as np
    from sklearn.linear_model import LinearRegression
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    # Use secrets to authorize with Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)

    # Load data from Google Sheet
    sheet = client.open("Groundswell-Business").worksheet("invoices")  # Adjust sheet name if needed
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Convert and prepare data
    df['Date created'] = pd.to_datetime(df['Date created'])
    forecast_df = df.groupby('Date created')['Grand total'].sum().reset_index()
    forecast_df.columns = ['ds', 'y']
    forecast_df['ds_ordinal'] = forecast_df['ds'].map(pd.Timestamp.toordinal)

    # Forecast using Linear Regression
    X = forecast_df[['ds_ordinal']]
    y = forecast_df['y']
    model = LinearRegression()
    model.fit(X, y)

    future_dates = pd.date_range(start=forecast_df['ds'].max() + pd.Timedelta(days=1), periods=30)
    future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
    predicted = model.predict(future_ordinals)

    # Combine historical + forecasted
    forecast = pd.DataFrame({'ds': future_dates, 'y': predicted})
    full_data = pd.concat([forecast_df[['ds', 'y']], forecast])

    # Display chart
    st.header("30-Day Revenue Forecast")
    st.line_chart(full_data.set_index('ds')['y'])


elif selection == "Ask AI":
    st.header("Ask AI About Your Invoices")

    import pandas as pd
    import json
    from openai import OpenAI

    # Load OpenAI client
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])

    # Example prompts for the user
    st.markdown("#### Try asking things like:")
    st.markdown("""
    - **How much has Millie paid?**  
    - **Show unpaid invoices**  
    - **Who are the top 5 paying students?**  
    - **How much does Lily owe?**  
    - **Show all invoices for Layla**  
    - **What’s the revenue by student?**  
    - **What was income last month?**
    """)

    # Query input
    query = st.text_input("Ask your question:")

    # Function to get intent and entities
    def get_intent_from_gpt(question):
        prompt = f"""
You are a helpful assistant for a dance school finance app.
Given a user question, return a JSON object with:
- an "intent"
- any relevant fields like "student" or "month"

Supported intents:
- 'total_paid': total amount paid by a student
- 'unpaid_invoices': list all unpaid invoices
- 'unpaid_by_student': unpaid invoices for a specific student
- 'summary_by_month': revenue grouped by month
- 'top_payers': top 5 paying students
- 'revenue_by_student': total revenue per student
- 'list_by_student': all invoices for a student

Respond ONLY with valid JSON.
User question: '{question}'
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5
        )
        return response.choices[0].message.content

    # Email generation helper
    def send_reminder_email(name, amount):
        prompt = f"""
Write a short, polite payment reminder email to {name}, who owes £{amount:.2f} for dance classes. 
Keep it friendly and professional. Mention that payment can be made online.
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content

    # Main logic
    if query:
        try:
            parsed = json.loads(get_intent_from_gpt(query))
            st.subheader("Intent Detected")
            st.json(parsed)

            intent = parsed.get("intent")

            if intent == "total_paid":
                name = parsed.get("student")
                result = df[(df["Student"].str.contains(name, case=False)) & (df["Status"] == "Paid")]
                total = result["Grand total"].sum()
                st.success(f"{name} has paid £{total:.2f}")

                show_followup(
                    label=f"Show all invoices for {name}",
                    callback=show_student_invoices,
                    student_name=name
                )

            elif intent == "unpaid_invoices":
                result = df[df["Status"] == "Unpaid"]
                st.dataframe(result)

                if not result.empty:
                    if st.button("Generate reminder emails for all students"):
                        names = result["Student"].unique()
                        for name in names:
                            amount = result[result["Student"] == name]["Grand total"].sum()
                            email = send_reminder_email(name, amount)
                            st.text_area(f"Email for {name}", email, height=150)

            elif intent == "unpaid_by_student":
                name = parsed.get("student")
                result = df[(df["Student"].str.contains(name, case=False)) & (df["Status"] == "Unpaid")]
                st.dataframe(result)

                if not result.empty:
                    if st.button(f"Generate reminder email for {name}"):
                        amount = result["Grand total"].sum()
                        email = send_reminder_email(name, amount)
                        st.text_area(f"Reminder email for {name}", email, height=150)

            elif intent == "summary_by_month":
                df["Month"] = pd.to_datetime(df["Date created"]).dt.to_period("M")
                summary = df.groupby("Month")["Grand total"].sum().sort_index()
                st.bar_chart(summary)

                st.markdown("**Want to see all invoices from the latest month?**")
                if st.button("Show invoices for latest month"):
                    latest_month = summary.index[-1]
                    invoices = df[df["Date created"].dt.to_period("M") == latest_month]
                    st.dataframe(invoices)

            elif intent == "top_payers":
                result = df[df["Status"] == "Paid"]
                summary = result.groupby("Student")["Grand total"].sum().sort_values(ascending=False).head(5)
                st.write("Top 5 paying students:")
                st.dataframe(summary)

            elif intent == "revenue_by_student":
                result = df[df["Status"] == "Paid"]
                summary = result.groupby("Student")["Grand total"].sum().sort_values(ascending=False)
                st.write("Revenue per student:")
                st.dataframe(summary)

            elif intent == "list_by_student":
                name = parsed.get("student")
                result = df[df["Student"].str.contains(name, case=False)]
                st.dataframe(result)

            else:
                st.warning("Sorry, I didn’t understand that question.")

        except Exception as e:
            st.error(f"Something went wrong: {e}")

elif selection == "Manager Dashboard":
    st.header("Manager Dashboard")

    # Revenue Summary
    df["Month"] = pd.to_datetime(df["Date created"]).dt.to_period("M")
    monthly_summary = df.groupby("Month")["Grand total"].sum().sort_index()
    st.subheader("Monthly Revenue")
    st.bar_chart(monthly_summary)

    latest_month = monthly_summary.index[-1]
    show_followup("Show invoices for latest month", show_invoices_by_month, latest_month)

    # Unpaid Overview
    st.subheader("Unpaid Invoices")
    unpaid_df = df[df["Status"] == "Unpaid"]
    st.dataframe(unpaid_df)

    top_unpaid = unpaid_df["Student"].value_counts().head(1).index[0]
    show_followup(f"Draft reminder email to {top_unpaid}", show_reminder_email, top_unpaid)

    # High-Value Invoices
    st.subheader("Invoices Over £100")
    show_followup("Show high-value invoices", show_high_value_invoices, 100)

    # Top Payers
    st.subheader("Top-Paying Students")
    paid_df = df[df["Status"] == "Paid"]
    top_students = paid_df.groupby("Student")["Grand total"].sum().sort_values(ascending=False).head(5)
    st.dataframe(top_students)


            
          

                    
                    
               


        
    
    



    
                    
                                           
