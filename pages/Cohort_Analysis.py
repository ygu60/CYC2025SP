import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Cohort Analysis Dashboard", layout="wide", page_icon="📊")

# Use blue-green gradient background that echoes heatmaps
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito Sans', sans-serif;
    background: linear-gradient(135deg, #e3f2fd 0%, #e8f5e9 100%);
    color: #1F3C4C;
}

h1, h2, h3 {
    color: #1F3C4C;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Cohort Analysis Dashboard")

# --- Check if donor data exists
if 'donor_data' not in st.session_state:
    st.warning("Please upload a donation file on the Home page first.")
    st.stop()
else:
    st.success("✅ Data loaded!")
    st.sidebar.markdown("### 📂 Files Processed:")
    for fname in st.session_state.get('uploaded_file_names', []):
        st.sidebar.markdown(f"• `{fname}`")

# --- Prepare Data
df = st.session_state['donor_data'].copy()
df = df.dropna(subset=['Date', 'Email'])

df['Donation Quarter'] = df['Date'].dt.to_period('Q').dt.start_time
df['Cohort Quarter'] = df.groupby('Email')['Donation Quarter'].transform('min')

first_quarter = df['Donation Quarter'].min()
last_quarter = df['Donation Quarter'].max()
quarter_range = pd.period_range(start=first_quarter.to_period('Q'), end=last_quarter.to_period('Q'), freq='Q')
total_quarters = len(quarter_range)

quarter_index_map = {q.to_timestamp(): i for i, q in enumerate(quarter_range)}
df['Global Quarter Index'] = df['Donation Quarter'].map(quarter_index_map)
df['Cohort Start Index'] = df['Cohort Quarter'].map(quarter_index_map)
df['Quarters Since First Donation'] = df['Global Quarter Index'] - df['Cohort Start Index']

# --- NxN Retention Matrix
cohort_retention = df.groupby(['Cohort Quarter', 'Quarters Since First Donation'])['Email'].nunique().unstack()
cohort_retention = cohort_retention.reindex(columns=range(total_quarters), fill_value=np.nan)
cohort_sizes = cohort_retention[0]
retention_matrix = cohort_retention.divide(cohort_sizes, axis=0) * 100

# Melt for Altair
retention_reset = retention_matrix.reset_index().melt(
    id_vars='Cohort Quarter', var_name='Quarter Index', value_name='Retention Rate (%)'
)
retention_reset['Cohort Label'] = retention_reset['Cohort Quarter'].dt.to_period('Q').astype(str)

# --- Monetary Heatmap
monetary_matrix = df.groupby(['Cohort Quarter', 'Quarters Since First Donation'])['Donation Amount'].sum().unstack()
monetary_matrix = monetary_matrix.reindex(columns=range(total_quarters), fill_value=np.nan)

monetary_reset = monetary_matrix.reset_index().melt(
    id_vars='Cohort Quarter', var_name='Quarter Index', value_name='Monetary Value'
)
monetary_reset['Cohort Label'] = monetary_reset['Cohort Quarter'].dt.to_period('Q').astype(str)

# --- Chart Tabs
tab1, tab2 = st.tabs(["📘 Retention Rate", "💵 Monetary Value"])

with tab1:
    st.subheader("📘 Donor Retention Heatmap")
    chart1 = alt.Chart(retention_reset).mark_rect().encode(
        x=alt.X('Quarter Index:O', title='Quarters Since First Donation'),
        y=alt.Y('Cohort Label:N', title='Cohort Start Quarter'),
        color=alt.Color('Retention Rate (%):Q', scale=alt.Scale(scheme='blues'), legend=alt.Legend(title='Retention %')),
        tooltip=['Cohort Label', 'Quarter Index', 'Retention Rate (%)']
    ).properties(width=700, height=400)

    st.altair_chart(chart1.configure_axis(labelColor='#1F3C4C', titleColor='#1F3C4C'), use_container_width=True)

with tab2:
    st.subheader("💵 Monetary Retention Heatmap")
    chart2 = alt.Chart(monetary_reset).mark_rect().encode(
        x=alt.X('Quarter Index:O', title='Quarters Since First Donation'),
        y=alt.Y('Cohort Label:N', title='Cohort Start Quarter'),
        color=alt.Color('Monetary Value:Q', scale=alt.Scale(scheme='greens'), legend=alt.Legend(title='Total $ Donated')),
        tooltip=['Cohort Label', 'Quarter Index', 'Monetary Value']
    ).properties(width=700, height=400)

    st.altair_chart(chart2.configure_axis(labelColor='#1F3C4C', titleColor='#1F3C4C'), use_container_width=True)

# --- Insight Text
st.markdown("""
### 🔍 Insights

These heatmaps show how well CVC retains donors both in terms of **number of people** and **donation value**:

- **Blue Map**: % of donors from a cohort who returned each quarter.
- **Green Map**: Total donation amount from those returning donors.

Use these to:
- Identify strong-performing donor groups.
- Spot seasonal giving patterns.
- Prioritize stewardship of high-value cohorts.
""")
