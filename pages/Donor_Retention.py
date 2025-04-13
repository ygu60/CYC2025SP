import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Donor Retention Dashboard", 
                   layout="wide", 
                   page_icon="🔁")
st.title("🔁 Donor Retention Dashboard")

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


# Load data  
if 'donor_data' not in st.session_state:
    st.warning("Please upload a donation file on the Home page first.")
    st.stop()
else:
    st.success("✅ Data loaded!")
    st.sidebar.markdown("### 📂 Files Processed:")
    for fname in st.session_state['uploaded_file_names']:
        st.sidebar.markdown(f"• `{fname}`")

df = st.session_state['donor_data']

# Original Retention Pie
st.subheader("🔁 Donor Retention Signals")
donor_dates = df.groupby('Email')['Date'].agg(['min', 'max', 'count'])
donor_dates['Retention Status'] = donor_dates['count'].apply(lambda x: 'Returning' if x > 1 else 'New')
retention_counts = donor_dates['Retention Status'].value_counts()
retention_data = retention_counts.reset_index()
retention_data.columns = ["Retention Status", "Count"]

retention_pie = alt.Chart(retention_data).mark_arc(innerRadius=50).encode(
    theta=alt.Theta(field="Count", type="quantitative"),
    color=alt.Color(field="Retention Status", type="nominal",
                    scale=alt.Scale(range=["#57B894", "#F25C54"])),
    tooltip=["Retention Status", "Count"]
).properties(height=300)

st.altair_chart(retention_pie.configure_legend(labelColor='#1F3C4C', titleColor='#1F3C4C'), use_container_width=True)

retention_n = st.selectbox("Number of donors to show in retention detail:", ['All', 10, 25, 50, 100], index=1, key="retention_detail")
with st.expander("See retention donor detail", expanded=False):
    st.dataframe(donor_dates.reset_index() if retention_n == 'All' else donor_dates.reset_index().head(retention_n))


# 🔄 Quarterly Churn Analysis
st.subheader("📆 Quarterly Churn Analysis")

st.markdown("""
**What is Churn Rate?**

Churn rate measures the percentage of previously active donors who did **not** return in the following quarter.  
It helps track how well CVC is retaining its donor base over time.

Understanding and minimizing churn is critical for:
- Building long-term donor relationships
- Improving fundraising predictability
- Reducing the cost of acquiring new donors

By identifying quarters with high donor churn, CVC can prioritize **outreach and re-engagement** campaigns more effectively.
""")

# Create a quarterly donor activity table
df['Quarter'] = df['Date'].dt.to_period('Q')
donor_quarters = df.groupby(['Email', 'Quarter']).size().unstack(fill_value=0)
donor_quarters = donor_quarters.applymap(lambda x: 1 if x > 0 else 0)

# Shift to find donor presence in next quarter
shifted = donor_quarters.shift(-1, axis=1)
churned = (donor_quarters == 1) & (shifted == 0)
retained = (donor_quarters == 1) & (shifted == 1)

# Calculate churn stats per quarter
churn_df = pd.DataFrame({
    'Quarter': donor_quarters.columns[:-1],
    'Churned Donors': churned.iloc[:, :-1].sum(),
    'Retained Donors': retained.iloc[:, :-1].sum()
})
churn_df['Total Prev Active'] = churn_df['Churned Donors'] + churn_df['Retained Donors']
churn_df['Churn Rate (%)'] = churn_df['Churned Donors'] / churn_df['Total Prev Active'] * 100

st.dataframe(churn_df.round(2), use_container_width=True)

# Chart: Churn rate over time
st.altair_chart(
    alt.Chart(churn_df).mark_line(point=True).encode(
        x='Quarter:T',
        y='Churn Rate (%):Q',
        tooltip=['Quarter', 'Churn Rate (%)']
    ).properties(height=350, title="Quarterly Churn Rate"),
    use_container_width=True
)

# Summary Stats
avg_churn = churn_df['Churn Rate (%)'].mean()
best_qtr_row = churn_df[churn_df['Churn Rate (%)'] == churn_df['Churn Rate (%)'].min()].iloc[0]
worst_qtr_row = churn_df[churn_df['Churn Rate (%)'] == churn_df['Churn Rate (%)'].max()].iloc[0]

st.markdown(f"""
**📊 Average Quarterly Churn Rate:** `{avg_churn:.1f}%`  

**Best Retention Quarter:** `{best_qtr_row['Quarter']}`  
Churn Rate: `{best_qtr_row['Churn Rate (%)']:.1f}%`

**Worst Retention Quarter:** `{worst_qtr_row['Quarter']}`  
Churn Rate: `{worst_qtr_row['Churn Rate (%)']:.1f}%`
""")