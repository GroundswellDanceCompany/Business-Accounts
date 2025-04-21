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
@st.cache_data(ttl=60)
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()

# Parse dates
df["Date created"] = pd.to_datetime(df["Date created"], errors="coerce")
df["Amount"] = pd.to_numeric(df["Grand total"], errors="coerce")
df["Status"] = df["Status"].fillna("Unpaid")

st.title("Dance School Invoice Dashboard")

# Filters
with st.sidebar:
    st.header("Filters")
    selected_status = st.multiselect("Payment Status", options=df["Status"].unique(), default=df["Status"].unique())
    students = df["Student"].unique().tolist()
    selected_students = st.multiselect("Students", options=students, default=students)
    min_date = df["Date"].min()
    max_date = df["Date"].max()
    selected_range = st.date_input("Date Range", value=(min_date, max_date))

# Apply filters
filtered_df = df[
    (df["Status"].isin(selected_status)) &
    (df["Student"].isin(selected_students)) &
    (df["Date"] >= pd.to_datetime(selected_range[0])) &
    (df["Date"] <= pd.to_datetime(selected_range[1]))
]

# KPI boxes
col1, col2, col3 = st.columns(3)
col1.metric("Total Invoiced", f"£{filtered_df['Amount'].sum():.2f}")
col2.metric("Paid", f"£{filtered_df[filtered_df['Status'] == 'Paid']['Amount'].sum():.2f}")
col3.metric("Unpaid", f"£{filtered_df[filtered_df['Status'] == 'Unpaid']['Amount'].sum():.2f}")

# Breakdown by student
st.subheader("Totals by Student")
student_summary = filtered_df.groupby("Student")["Amount"].sum().reset_index().sort_values(by="Amount", ascending=False)
st.dataframe(student_summary)

# Monthly trend
st.subheader("Monthly Invoicing Trend")
monthly = filtered_df.groupby(filtered_df["Date"].dt.to_period("M"))["Amount"].sum().reset_index()
monthly["Date"] = monthly["Date"].astype(str)
st.line_chart(monthly.set_index("Date"))

# Status distribution
st.subheader("Invoice Status Distribution")
st.bar_chart(filtered_df["Status"].value_counts())

# Full data view
with st.expander("See Full Data"):
    st.dataframe(filtered_df)

# Export option
st.download_button("Download Filtered Data as CSV", data=filtered_df.to_csv(index=False), file_name="invoices_filtered.csv", mime="text/csv")
