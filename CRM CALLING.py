import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from datetime import datetime
import pytz

# -------------------------
# CONFIG
# -------------------------
SHEET_ID = "1jwfAPG4e59_mIwDIpxoaXQ_blgxCsdEUsA9oW7yeJFQ"
DS_SHEET = "DS"
STORE_SHEET = "STORE"

st.set_page_config(layout="wide")

# -------------------------
# GOOGLE CONNECTION
# -------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(SHEET_ID)
ds = sheet.worksheet(DS_SHEET)
store = sheet.worksheet(STORE_SHEET)

# -------------------------
# LOAD DATA
# -------------------------
data = ds.get_all_records()
df = pd.DataFrame(data)

# -------------------------
# FILTER VALID ROWS
# -------------------------
df = df[
    (df["DUE DATE"] != "") &
    (df["BILL NUMBER"] != "")
]

# -------------------------
# DATE PARSING
# -------------------------
df["DUE DATE"] = pd.to_datetime(df["DUE DATE"], format="%d-%m-%Y", errors='coerce')
df["CALLING AFTER +10 DAYS"] = pd.to_datetime(df["CALLING AFTER +10 DAYS"], format="%d-%m-%Y", errors='coerce')
df["CALLING AFTER +20 DAYS"] = pd.to_datetime(df["CALLING AFTER +20 DAYS"], format="%d-%m-%Y", errors='coerce')

today = pd.to_datetime("today").normalize()

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def safe_value(val):
    if pd.isna(val):
        return ""
    return str(val)

def format_date(val):
    if pd.isna(val):
        return ""
    if isinstance(val, pd.Timestamp):
        return val.strftime("%d-%b-%Y")
    return str(val)

# -------------------------
# UI TITLE
# -------------------------
st.title("📞 CALL TRACKING SYSTEM")

# -------------------------
# FILTER UI
# -------------------------
st.subheader("🔍 Filters")

colf1, colf2, colf3, colf4 = st.columns(4)

with colf1:
    party_filter = st.selectbox(
        "PARTY NAME",
        ["ALL"] + sorted(df["PARTY NAME"].dropna().unique())
    )

with colf2:
    agent_filter = st.selectbox(
        "AGENT NAME",
        ["ALL"] + sorted(df["AGENT NAME"].dropna().unique())
    )

with colf3:
    bill_filter = st.selectbox(
        "BILL NUMBER",
        ["ALL"] + sorted(df["BILL NUMBER"].dropna().unique())
    )

with colf4:
    date_option = st.selectbox(
        "CALL DATE FILTER",
        ["ALL DATES", f"Today ({datetime.now().strftime('%d-%b-%Y')})", "Select Date"]
    )

    selected_date = None

    if date_option == "Select Date":
        selected_date = st.date_input("Choose Date")

    elif "Today" in date_option:
        selected_date = today

# -------------------------
# APPLY FILTERS
# -------------------------
if party_filter != "ALL":
    df = df[df["PARTY NAME"] == party_filter]

if agent_filter != "ALL":
    df = df[df["AGENT NAME"] == agent_filter]

if bill_filter != "ALL":
    df = df[df["BILL NUMBER"] == bill_filter]

# DATE FILTER LOGIC
if selected_date is not None:
    selected_date = pd.to_datetime(selected_date)

    df = df[
        (df["CALLING AFTER +10 DAYS"] == selected_date) |
        (df["CALLING AFTER +20 DAYS"] == selected_date)
    ]

# -------------------------
# DISPLAY DATA
# -------------------------
for i, row in df.iterrows():

    # Conditional color
    color = ""
    if pd.notna(row["CALLING AFTER +10 DAYS"]) and row["CALLING AFTER +10 DAYS"] >= today:
        color = "#f4c2c2"
    if pd.notna(row["CALLING AFTER +20 DAYS"]) and row["CALLING AFTER +20 DAYS"] >= today:
        color = "#f4c2c2"

    st.markdown(
        f'<div style="background-color:{color}; padding:10px; border-radius:10px;">',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([5, 3, 2])

    with col1:
        st.write(f"**PARTY:** {row['PARTY NAME']}")
        st.write(f"**AGENT:** {row['AGENT NAME']}")
        st.write(f"**AMOUNT:** {row['OUTSTANDING AMOUNT']}")
        st.write(f"**DUE DATE:** {format_date(row['DUE DATE'])}")
        st.write(f"**BILL NO:** {row['BILL NUMBER']}")

        st.write(f"📅 CALL AFTER +10 DAYS: {format_date(row['CALLING AFTER +10 DAYS'])}")
        st.write(f"📅 CALL AFTER +20 DAYS: {format_date(row['CALLING AFTER +20 DAYS'])}")

    with col2:
        remark = st.text_input("REMARK", key=f"remark_{i}")

    with col3:
        if st.button("CALL DONE", key=f"btn_{i}"):

            # timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            ist = pytz.timezone("Asia/Kolkata")
            # timestamp = datetime.now(ist).strftime("%d-%b-%Y %H:%M:%S")
            timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
            
            new_row = [
                safe_value(row["PARTY NAME"]),
                safe_value(row["AGENT NAME"]),
                safe_value(row["OUTSTANDING AMOUNT"]),
                format_date(row["DUE DATE"]),
                safe_value(row["BILL NUMBER"]),
                format_date(row["CALLING AFTER +10 DAYS"]),
                format_date(row["CALLING AFTER +20 DAYS"]),
                timestamp,
                safe_value(remark)
            ]

            # store.append_row(new_row)
            store.append_row(new_row, value_input_option="USER_ENTERED")

            st.success("Stored Successfully ✅")

    st.markdown("</div>", unsafe_allow_html=True)
