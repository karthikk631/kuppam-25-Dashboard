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

# ---------------- CONFIGS ----------------
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

# ---------------- SUMMARY METRICS ----------------
st.markdown("---")
st.subheader("📈 Summary")
col1, col2, col3 = st.columns(3)
col1.metric("👶 Total Children", len(df))
col2.metric("🏫 Total AWCs", df["Name of AWC"].nunique())
col3.metric("⚠️ Children with Delay", df["Has_Delay"].sum())

# ---------------- GENDER PIE ----------------
st.markdown("#### 👧👦 Gender Distribution")
gender_count = df["CHINFO_GENDER"].value_counts()
fig_gender = px.pie(names=gender_count.index, values=gender_count.values, title="Gender Split")
st.plotly_chart(fig_gender, use_container_width=True)

# ---------------- DELAY PIE ----------------
st.markdown("#### 🧠 Delay Type Breakdown")
delay_summary = df[delay_cols].lt(0).sum().rename(index=delay_labels)
fig_delay = px.pie(
    names=delay_summary.index,
    values=delay_summary.values,
    title="Total Delays by Category",
    hole=0.4
)
st.plotly_chart(fig_delay, use_container_width=True)

# ---------------- DELAY CATEGORY BUTTONS ----------------
st.subheader("📌 View Children by Delay Category")
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

# ---------------- DELAY COUNT CHART ----------------
st.subheader("🔢 Delay Count Distribution")
delay_counts = df["Total Delays"].value_counts().sort_index()
fig_delay_bar = px.bar(x=delay_counts.index, y=delay_counts.values, labels={"x": "Number of Delays", "y": "Children"}, title="Delay Count Overview")
st.plotly_chart(fig_delay_bar, use_container_width=True)

# ---------------- DELAY COUNT FILTER ----------------
st.markdown("#### Click on Delay Count to View Children")
count_selection = None
count_columns = st.columns(5)
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
st.subheader("🏫 Multi-AWC Center Filter")
awc_selected = st.multiselect("Select One or More AWC Centers", options=sorted(df["Name of AWC"].dropna().unique()))

if awc_selected:
    filtered_df = df[df["Name of AWC"].isin(awc_selected)]
    st.write(f"📍 Showing data for {len(filtered_df)} children across {len(awc_selected)} centers")

    col1, col2, col3 = st.columns(3)
    col1.metric("👶 Children", len(filtered_df))
    col2.metric("⚠️ With Delay", filtered_df["Has_Delay"].sum())
    col3.metric("🧠 Delay %", f"{round((filtered_df['Has_Delay'].sum()/len(filtered_df))*100, 1)}%")

    # Delay category stacked bar
    delay_bar = filtered_df[delay_cols].lt(0).sum().rename(index=delay_labels).reset_index()
    delay_bar.columns = ["Delay Type", "Count"]
    fig_bar = px.bar(delay_bar, x="Delay Type", y="Count", title="Selected AWC – Delay Type Distribution", color="Delay Type")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Delay Count Distribution (pie)
    count_dist = filtered_df["Total Delays"].value_counts().sort_index()
    fig_count_pie = px.pie(names=count_dist.index, values=count_dist.values, title="Delay Count in Selected AWCs")
    st.plotly_chart(fig_count_pie, use_container_width=True)

# ---------------- AWC-WISE BAR ----------------
st.markdown("---")
st.subheader("🏫 AWC-wise Delay Overview")
awc_summary = df[df["Has_Delay"]].groupby("Name of AWC")["Has_Delay"].count().sort_values(ascending=False)
fig_awc = px.bar(x=awc_summary.index, y=awc_summary.values, labels={"x": "AWC", "y": "Children with Delay"}, title="Delays per AWC")
st.plotly_chart(fig_awc, use_container_width=True)

# ---------------- AGE GROUP ANALYSIS ----------------
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
st.dataframe(age_group_summary.rename(columns={"Total": "Total Children", "With_Delays": "Children with Delays"}), use_container_width=True)

# 📊 Age group pie chart
fig_age_pie = px.pie(age_group_summary, names="Age Group", values="With_Delays", title="Delays by Age Group")
st.plotly_chart(fig_age_pie, use_container_width=True)

# ---------------- FULL TABLE ----------------
st.markdown("---")
st.subheader("📋 View All Children")
awc_all = st.selectbox("Select AWC to view", options=["All"] + sorted(df["Name of AWC"].dropna().unique()))
final_df = df[df["Name of AWC"] == awc_all] if awc_all != "All" else df
view_all = final_df[[ "ID", "Child Name", "Parent Name", "Phone Number", "Name of AWC", "Total Delays"] + delay_cols].rename(columns=delay_labels)
st.dataframe(view_all, use_container_width=True)

st.markdown("---")
st.caption("🚀 Built by CareNGrow Team")
