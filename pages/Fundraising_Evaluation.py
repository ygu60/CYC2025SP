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
else:
    st.success("✅ Data loaded!")
    st.sidebar.markdown("### 📂 Files Processed:")
    for fname in st.session_state['uploaded_file_names']:
        st.sidebar.markdown(f"• `{fname}`")


df = st.session_state['donor_data'].copy()
df = df.dropna(subset=['Date', 'Donation Amount'])

# -- Section: Fundraising by Campaign --
st.subheader("🎯 Total Raised & Average Gift by Campaign")

campaign_df = df.groupby("Campaign Title")["Donation Amount"].agg(['sum', 'mean', 'count']).reset_index()
campaign_df.rename(columns={"sum": "Total Raised", "mean": "Average Gift", "count": "Donations"}, inplace=True)

# Add this to handle NaNs
campaign_df = campaign_df.fillna(0)

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

import re

# -- Section: Year-over-Year Growth by Campaign --
st.subheader("📊 Year-over-Year (YoY) Growth by Campaign")

# Use correct date column and ensure datetime
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Donation Year'] = df['Date'].dt.year

# Determine which campaign column exists
campaign_col = 'Campaign' if 'Campaign' in df.columns else 'Campaign Title'

if campaign_col in df.columns:
    # Strip year from campaign names
    def clean_campaign(name):
        return re.sub(r'\s*\d{4}$', '', str(name))  # Remove 4-digit year at the end

    df['Campaign Clean'] = df[campaign_col].apply(clean_campaign)

    # Group by cleaned name and year
    yoy_df = df.groupby(['Campaign Clean', 'Donation Year'])['Donation Amount'].sum().reset_index()

    # Fill missing combinations with 0s
    all_years = sorted(df['Donation Year'].dropna().unique())
    all_campaigns = df['Campaign Clean'].dropna().unique()
    full_index = pd.MultiIndex.from_product([all_campaigns, all_years], names=['Campaign Clean', 'Donation Year'])
    yoy_df = yoy_df.set_index(['Campaign Clean', 'Donation Year']).reindex(full_index, fill_value=0).reset_index()

    # Campaign selector
    selected_campaign = st.selectbox("Select a Campaign", sorted(all_campaigns))

    filtered_df = yoy_df[yoy_df['Campaign Clean'] == selected_campaign]

    # Bar chart
    bar_chart = alt.Chart(filtered_df).mark_bar(color="#F57C00").encode(
        x=alt.X('Donation Year:O', title='Year'),
        y=alt.Y('Donation Amount:Q', title='Total Donations'),
        tooltip=['Campaign Clean', 'Donation Year', 'Donation Amount']
    ).properties(
        title=f"Year-over-Year Donations: {selected_campaign}",
        height=400
    )

    st.altair_chart(bar_chart, use_container_width=True)

else:
    st.warning("No campaign column found in data.")
