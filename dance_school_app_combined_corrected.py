import streamlit as st

st.set_page_config(page_title="Dance School OS", layout="wide")

tabs = ["Invoice Generator", "Dashboard", "Student Manager", "Registers", "Accounts Dashboard"]
selection = st.sidebar.radio("Choose View", tabs)

if selection == "Invoice Generator":
    import json
    import streamlit as st
    import gspread
    import pandas as pd
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
        ],   
        "Session-Based": [
            "Extra Rehearsal - Competition",
            "Extra Rehearsal - Show",
            "Private Lesson"
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
        invoice_label = f"{student} - {invoice_start.strftime('%b %Y')}"
        row = [date_created, invoice_period, student, class_names, classes_attended, total_class_rate, extra_names, extras_total, grand_total, "Unpaid", notes, invoice_label]
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

elif selection == "Dashboard":
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

elif selection == "Accounts Dashboard":
    if st.session_state.get("refresh_expenses"):
        st.session_state["refresh_expenses"] = False
        
    import streamlit as st
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import pandas as pd
    from datetime import datetime
    import calendar

    st.subheader("Add New Expense")

    with st.form("expense_entry_form", clear_on_submit=True):
        expense_date = st.date_input("Date of Expense")
        category = st.selectbox("Category", ["Costumes", "Studio Rent", "Music Subscriptions", "Travel", "Other"])
        description = st.text_input("Description")
        amount = st.number_input("Amount (£)", min_value=0.0, step=0.5)
        receipt_url = st.text_input("Receipt URL (optional)")
        submit_expense = st.form_submit_button("Add Expense")

        if submit_expense and expense_date and category and description and amount:
            expenses_sheet.append_row([
                str(expense_date),
                category,
                description,
                f"{amount:.2f}",
                receipt_url
            ])
            st.success("Expense added successfully!")
            st.rerun()

    st.header("Accounts Dashboard (Expenses Tracker)")

    # Google Sheets connection
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    expenses_sheet = client.open("Groundswell-Business").worksheet("expenses")

    # Load expense data
    data = expenses_sheet.get_all_records()
    if not data:
        st.info("No expenses data found.")
    else:
        expenses = pd.DataFrame(data)

        # Ensure column names are clean
        expenses.columns = [col.strip() for col in expenses.columns]

        if "Date" not in expenses.columns:
            st.error("Missing 'Date' column in your sheet.")
        else:
            expenses["Date"] = pd.to_datetime(expenses["Date"], errors="coerce")
            expenses["Amount"] = pd.to_numeric(expenses["Amount"], errors="coerce")
            expenses["Year"] = expenses["Date"].dt.year.astype("Int64")
            expenses["Month"] = expenses["Date"].dt.month

            st.subheader("Filter by Month and Year")
            current_year = datetime.now().year
            year_selected = st.selectbox("Year", sorted(expenses["Year"].dropna().unique(), reverse=True), index=0)
            month_selected = st.selectbox("Month", list(calendar.month_name)[1:])

            month_num = list(calendar.month_name).index(month_selected)
            filtered = expenses[(expenses["Month"] == month_num) & (expenses["Year"] == year_selected)]

            st.subheader(f"Expenses for {month_selected} {year_selected}")
            st.dataframe(filtered)

            total_month = filtered["Amount"].sum()
            st.metric(label="Total This Month", value=f"£{total_month:.2f}")

            st.subheader("Year-to-Date Summary")
            ytd = expenses[expenses["Year"] == year_selected]
            ytd_summary = ytd.groupby("Month")["Amount"].sum().reindex(range(1, 13), fill_value=0)

            st.line_chart(ytd_summary)

            st.subheader("Add New Expense")
            with st.form("add_expense"):
                exp_date = st.date_input("Date", value=datetime.today())
                category = st.selectbox("Category", ["Studio Rent", "Costumes", "Music License", "Travel", "Admin", "Other"])
                desc = st.text_input("Description")
                amt = st.number_input("Amount", min_value=0.0, step=0.5)
                receipt_url = st.text_input("Receipt URL (optional)")

                submit_exp = st.form_submit_button("Add Expense")
                if submit_exp:
                    expenses_sheet.append_row([exp_date.strftime("%Y-%m-%d"), category, desc, amt, receipt_url])
                    st.success("Expense added successfully.")
                    st.session_state["refresh_expenses"] = True
                    
                                           
