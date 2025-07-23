import streamlit as st
import pandas as pd
import plotly.express as px

# ✅ Login users
USERS = {
    "admin": "admin123",
    "team": "cng2025",
    "meghana": "hello123"
}

def login():
    st.title("🔐 Login to CareNGrow Dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if username in USERS and USERS[username] == password:
            st.session_state["logged_in"] = True
            st.success(f"✅ Welcome, {username}!")
        else:
            st.error("❌ Invalid credentials.")

# ✅ Protect everything behind login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="CareNGrow Dashboard", layout="wide")
st.title("🧠 Kuppam Child Development Dashboard")

# ---------------------- LOAD DATA ----------------------
@st.cache_data
def load_data():
    df = pd.read_excel("Kuppam_Pilot_Data_with_Names_AWC.xlsx")
    df["CHINFO_GENDER"] = df["CHINFO_GENDER"].replace({
        1: "Male", 2: "Female", "FAMALE": "Female", "MALU": "Male"
    })
    return df

df = load_data()

# ---------------------- CONFIGS ----------------------
delay_cols = ['Code_CG_DELAY', 'Code_LC_DELAY', 'Code_MT_DELAY', 'Code_SE_DELAY']
delay_labels = {
    'Code_CG_DELAY': 'Cognitive',
    'Code_LC_DELAY': 'Language/Communication',
    'Code_MT_DELAY': 'Motor',
    'Code_SE_DELAY': 'Social-Emotional'
}
reverse_delay_labels = {v: k for k, v in delay_labels.items()}

df["Total Delays"] = df[delay_cols].lt(0).sum(axis=1)
df["Has_Delay"] = df["Total Delays"] > 0

# ---------------------- METRIC CARDS ----------------------
st.markdown("---")
st.subheader("📊 Overall Summary")
col1, col2, col3 = st.columns(3)
col1.metric("👶 Total Children", len(df))
col2.metric("🏫 Total AWCs", df["Name of AWC"].nunique())
col3.metric("⚠️ Children with Delay", df["Has_Delay"].sum())

# ---------------------- GENDER DISTRIBUTION ----------------------
st.markdown("---")
st.subheader("👧👦 Gender Distribution")
gender_count = df["CHINFO_GENDER"].value_counts()
fig_gender = px.pie(
    names=gender_count.index,
    values=gender_count.values,
    title="Gender Breakdown"
)
st.plotly_chart(fig_gender, use_container_width=True)

# ---------------------- DELAY CARDS (CLICKABLE) ----------------------
st.markdown("---")
st.subheader("🧠 Delay Categories – Click to Explore")
delay_selection = None
columns = st.columns(4)
for i, col in enumerate(delay_cols):
    count = (df[col] < 0).sum()
    label = delay_labels[col]
    if columns[i].button(f"{label} ({count})"):
        delay_selection = label

if delay_selection:
    st.markdown(f"### 👇 Children with **{delay_selection}** Delay")
    selected_col = reverse_delay_labels[delay_selection]
    delay_filtered = df[df[selected_col] < 0]
    display_df = delay_filtered[[
        "Child Name", "Parent Name", "Phone Number", "Name of AWC", "Total Delays"
    ] + delay_cols].rename(columns=delay_labels)

    def style_delay(val): return 'background-color: #ffcccc' if val < 0 else ''
    styled_df = display_df.style.applymap(style_delay, subset=list(delay_labels.values()))

    st.dataframe(styled_df, use_container_width=True)


# ---------------------- HISTOGRAM ----------------------
st.markdown("---")
st.subheader("📌 Delay Count Distribution")
fig_hist = px.histogram(df, x='Total Delays', nbins=5, title="Children by Number of Delays")
st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------- AWC DELAY OVERVIEW ----------------------
st.markdown("---")
st.subheader("🏫 AWC-wise Delay Chart")
awc_summary = df[df["Has_Delay"]].groupby("Name of AWC")["Has_Delay"].count().sort_values(ascending=False)
fig_awc = px.bar(
    x=awc_summary.index,
    y=awc_summary.values,
    labels={"x": "AWC Center", "y": "Children with Delay"},
    title="Delays per Anganwadi Center"
)
st.plotly_chart(fig_awc, use_container_width=True)

awc_selected = st.selectbox("🔍 View Children in a Specific AWC", options=["None"] + list(awc_summary.index))
if awc_selected != "None":
    awc_df = df[(df["Name of AWC"] == awc_selected) & (df["Has_Delay"])]
    display_awc = awc_df[[
        "Child Name", "Parent Name", "Phone Number", "Name of AWC", "Total Delays"
    ] + delay_cols].rename(columns=delay_labels)
    st.dataframe(display_awc)

# ---------------------- FULL TABLE FILTER ----------------------
st.markdown("---")
st.subheader("📋 View All Children by AWC")
awc_all = st.selectbox("Select Any AWC to View Full List", options=["All"] + sorted(df["Name of AWC"].dropna().unique()))
final_df = df[df["Name of AWC"] == awc_all] if awc_all != "All" else df
view_all = final_df[[
    "Child Name", "Parent Name", "Phone Number", "Name of AWC", "Total Delays"
] + delay_cols].rename(columns=delay_labels)

st.dataframe(view_all, use_container_width=True)

st.markdown("---")
st.caption("🚀 Built by CareNGrow Team")
