import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Fundraising Evaluation", layout="wide", page_icon="📈")
st.title("📈 Fundraising Evaluation")

# -- Style --
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Nunito Sans', sans-serif;
        background-color: #ffffff;
        color: #1F3C4C !important;
    }
    </style>
""", unsafe_allow_html=True)

# -- Load data --
if 'donor_data' not in st.session_state:
    st.warning("Please upload a donation file on the Home page first.")
    st.stop()

df = st.session_state['donor_data'].copy()
df = df.dropna(subset=['Date', 'Donation Amount'])

# -- Section: Fundraising by Campaign --
st.subheader("🎯 Total Raised & Average Gift by Campaign")

campaign_df = df.groupby("Campaign Title")["Donation Amount"].agg(['sum', 'mean', 'count']).reset_index()
campaign_df.rename(columns={"sum": "Total Raised", "mean": "Average Gift", "count": "Donations"}, inplace=True)

col1, col2 = st.columns(2)
with col1:
    st.altair_chart(
        alt.Chart(campaign_df).mark_bar().encode(
            x=alt.X("Total Raised:Q", title="Total Raised"),
            y=alt.Y("Campaign Title:N", sort='-x'),
            tooltip=["Campaign Title", "Total Raised"]
        ).properties(height=350),
        use_container_width=True
    )

with col2:
    st.altair_chart(
        alt.Chart(campaign_df).mark_bar(color="#6096BA").encode(
            x=alt.X("Average Gift:Q", title="Average Gift ($)"),
            y=alt.Y("Campaign Title:N", sort='-x'),
            tooltip=["Campaign Title", "Average Gift"]
        ).properties(height=350),
        use_container_width=True
    )

# -- Section: Donation Amount Distribution --
st.subheader("💸 Donation Size Distribution")

bin_width = st.slider("Select bin width for histogram ($):", 5, 500, 50, step=5)
hist_data = df[df["Donation Amount"] <= 1000]  # Filter out outliers for visualization

hist = alt.Chart(hist_data).mark_bar(opacity=0.7).encode(
    alt.X("Donation Amount:Q", bin=alt.Bin(step=bin_width), title="Donation Amount ($)"),
    alt.Y("count()", title="Frequency"),
    tooltip=["count()"]
).properties(height=350)

st.altair_chart(hist, use_container_width=True)

# -- Section: Cumulative Fundraising Trend --
st.subheader("📈 Fundraising Over Time")

df['Month'] = df['Date'].dt.to_period('M').dt.to_timestamp()
monthly = df.groupby('Month')['Donation Amount'].sum().reset_index()
monthly['Cumulative'] = monthly['Donation Amount'].cumsum()

line = alt.Chart(monthly).mark_line(point=True).encode(
    x=alt.X("Month:T", title="Month"),
    y=alt.Y("Cumulative:Q", title="Cumulative Donations"),
    tooltip=["Month", "Cumulative"]
).properties(height=350)

st.altair_chart(line, use_container_width=True)

# -- Section: Year-over-Year Growth by Campaign --
st.subheader("📊 Year-over-Year (YoY) Growth by Campaign")

df['Year'] = df['Date'].dt.year
pivot = df.pivot_table(index='Campaign Title', columns='Year', values='Donation Amount', aggfunc='sum')

# Calculate YoY Growth safely
growth = pd.DataFrame(index=pivot.index)
years = sorted(pivot.columns.tolist())

for i in range(1, len(years)):
    prev = years[i - 1]
    curr = years[i]
    growth[curr] = ((pivot[curr] - pivot[prev]) / pivot[prev].replace({0: pd.NA})) * 100

growth.reset_index(inplace=True)
growth_melted = growth.melt(id_vars='Campaign Title', var_name='Year', value_name='YoY Growth (%)')
growth_melted.dropna(inplace=True)

# Plot
growth_chart = alt.Chart(growth_melted).mark_bar().encode(
    x=alt.X('Year:O'),
    y=alt.Y('YoY Growth (%):Q'),
    color=alt.Color('Campaign Title:N', legend=alt.Legend(title="Campaign")),
    tooltip=['Campaign Title', 'Year', 'YoY Growth (%)']
).properties(height=350)

st.altair_chart(growth_chart, use_container_width=True)
