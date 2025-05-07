
elif selection == "Student Manager":
    import pandas as pd
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from datetime import date
    import streamlit as st

    st.header("Student & Class Management")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    students_sheet = client.open("Groundswell-Business").worksheet("students")
    classes_sheet = client.open("Groundswell-Business").worksheet("class_enrollments")

    students_data = students_sheet.get_all_records()
    student_names = [s["Name"] for s in students_data if s.get("Name")]

    def calculate_age_group(dob):
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age <= 5:
            return "Mini (3-5)"
        elif age <= 12:
            return "Junior (6-12)"
        elif age <= 16:
            return "Teen (13-16)"
        else:
            return "Adult"

    st.subheader("Add / Edit Student")
    with st.form("student_form", clear_on_submit=True):
        name = st.text_input("Name")
        dob = st.date_input("Date of Birth", value=date(2010, 1, 1), min_value=date(2000, 1, 1), max_value=date.today())
        contact = st.text_input("Contact")
        notes = st.text_area("Notes")
        submit = st.form_submit_button("Save Student")

        if submit and name:
            age_group = calculate_age_group(dob)
            students_sheet.append_row([name, str(dob), age_group, contact, notes])
            st.success(f"Student '{name}' added successfully!")

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
    except Exception as e:
        st.error(f"Error loading roster: {e}")
