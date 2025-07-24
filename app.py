import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- LOGIN ----------------
USERS = {
    "admin": "admin123",
    "team": "cng2025",
    "meghana": "hello123"
}

def login():
    st.image("logo.jpg", width=260)
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

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="CareNGrow Dashboard", layout="wide")
st.title("📊 Kuppam Child Development Dashboard")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("📤 Upload Excel file", type=["xlsx"])
if not uploaded_file:
    st.warning("⚠️ Please upload the latest Excel data to continue.")
    st.stop()

# ---------------- LOAD & CLEAN DATA ----------------
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df["CHINFO_GENDER"] = df["CHINFO_GENDER"].replace({
        1: "Male", 2: "Female", "FAMALE": "Female", "MALU": "Male"
    })
    return df

df = load_data(uploaded_file)

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

# ---------------- METRICS ----------------
st.markdown("---")
st.subheader("📈 Summary")
col1, col2, col3 = st.columns(3)
col1.metric("👶 Total Children", len(df))
col2.metric("🏫 Total AWCs", df["Name of AWC"].nunique())
col3.metric("⚠️ Children with Delay", df["Has_Delay"].sum())

# ---------------- GENDER PIE ----------------
st.markdown("---")
st.subheader("👧👦 Gender Distribution")
gender_count = df["CHINFO_GENDER"].value_counts()
fig_gender = px.pie(names=gender_count.index, values=gender_count.values, title="Gender")
st.plotly_chart(fig_gender, use_container_width=True)

# ---------------- DELAY CATEGORY CARDS ----------------
st.markdown("---")
st.subheader("🧠 Delay Categories (Click to Filter)")
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
    display_df = delay_filtered[[ "ID", "Child Name", "Parent Name", "Phone Number", "Name of AWC", "Total Delays"] + delay_cols].rename(columns=delay_labels)
    def style_delay(val): return 'background-color: #ffcccc' if val < 0 else ''
    st.dataframe(display_df.style.applymap(style_delay, subset=list(delay_labels.values())), use_container_width=True)

# ---------------- DELAY COUNT CARDS ----------------
st.markdown("---")
st.subheader("🔢 Delay Count Summary")
count_columns = st.columns(5)
count_selection = None
for i in range(5):
    count = (df["Total Delays"] == i).sum()
    if count_columns[i].button(f"{i} Delay{'s' if i != 1 else ''} ({count})"):
        count_selection = i

if count_selection is not None:
    st.markdown(f"### 👇 Children with **{count_selection}** Delay(s)")
    count_df = df[df["Total Delays"] == count_selection][["ID", "Child Name", "Parent Name", "Phone Number", "Name of AWC", "Total Delays"] + delay_cols].rename(columns=delay_labels)
    st.dataframe(count_df, use_container_width=True)

# ---------------- MULTI-CENTER AWC FILTER ----------------
st.markdown("---")
st.subheader("🏫 Filter by AWC (Multiple Selection)")
awc_selected = st.multiselect("Select One or More AWC Centers", options=sorted(df["Name of AWC"].dropna().unique()))

if awc_selected:
    filtered_df = df[df["Name of AWC"].isin(awc_selected)]
    st.write(f"📍 Showing data for {len(filtered_df)} children across {len(awc_selected)} centers")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("👶 Children", len(filtered_df))
    col2.metric("⚠️ With Delay", filtered_df["Has_Delay"].sum())
    col3.metric("🧠 Delay %", f"{round((filtered_df['Has_Delay'].sum()/len(filtered_df))*100, 1)}%")

    # Delay Breakdown
    st.markdown("#### Delay Categories")
    delay_bar = filtered_df[delay_cols].lt(0).sum().rename(index=delay_labels).reset_index()
    delay_bar.columns = ["Delay Type", "Count"]
    st.bar_chart(delay_bar.set_index("Delay Type"))

    # Delay Count Table
    st.markdown("#### Delay Count Distribution")
    delay_count_table = filtered_df["Total Delays"].value_counts().sort_index().reset_index()
    delay_count_table.columns = ["# of Delays", "# of Children"]
    st.dataframe(delay_count_table)

# ---------------- AWC-WISE BAR CHART ----------------
st.markdown("---")
st.subheader("🏫 AWC-wise Delay Overview")
awc_summary = df[df["Has_Delay"]].groupby("Name of AWC")["Has_Delay"].count().sort_values(ascending=False)
fig_awc = px.bar(x=awc_summary.index, y=awc_summary.values, labels={"x": "AWC", "y": "Children with Delay"}, title="AWC Delay Distribution")
st.plotly_chart(fig_awc, use_container_width=True)

# ---------------- AGE GROUP TABLE ----------------
st.markdown("---")
st.subheader("🍼 Age Group-wise Delay Analysis")

age_bins = [0, 12, 24, 36, 48, 60, float("inf")]
age_labels = ["0–12m", "13–24m", "25–36m", "37–48m", "49–60m", "61–72m"]
df["Age Group"] = pd.cut(df["Code_Age"], bins=age_bins, labels=age_labels, right=True, include_lowest=True)

age_group_summary = (
    df.groupby("Age Group")
    .agg(Total=("ID", "count"),
         With_Delays=("Has_Delay", "sum"))
    .reset_index()
)
age_group_summary["Percentage"] = (age_group_summary["With_Delays"] / age_group_summary["Total"] * 100).round(1).astype(str) + "%"
age_group_summary.columns = ["Age Group", "Total", "With Delays", "Percentage"]
st.dataframe(age_group_summary, use_container_width=True)

# ---------------- FULL TABLE VIEW ----------------
st.markdown("---")
st.subheader("📋 Full Data Table")
awc_all = st.selectbox("Select AWC to view", options=["All"] + sorted(df["Name of AWC"].dropna().unique()))
final_df = df[df["Name of AWC"] == awc_all] if awc_all != "All" else df
view_all = final_df[[ "ID", "Child Name", "Parent Name", "Phone Number", "Name of AWC", "Total Delays"] + delay_cols].rename(columns=delay_labels)
st.dataframe(view_all, use_container_width=True)

st.markdown("---")
st.caption("🚀 Built by CareNGrow Team")
