import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(
    page_title="CVC Donor Insights Dashboard",
    layout="wide",
    page_icon="📊"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Nunito Sans', sans-serif;
        background-color: #ffffff;
        color: #1F3C4C !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        background-color: #fdfdfd;
    }
    .section-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 2rem;
    }
    .metric-container {
        display: flex;
        gap: 1.5rem;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    .metric-container > div {
        flex: 1;
        background: #fefefe;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
        border-top: 6px solid #FDBA21;
    }
    h1, h2, h3, .st-subheader {
        color: #1F3C4C;
    }
    .stMetric {
        color: #1F3C4C;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Crime Victim Center - Donor Insights Dashboard")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/Donor_Retention.py", label="🔁 Retention")

with col2:
    st.page_link("pages/Donor_Demographics.py", label="🌍 Demographics")

with col3:
    st.page_link("pages/Fundraising_Evaluation.py", label="📈 Fundraising")

with col4:
    st.page_link("pages/Cohort_Analysis.py", label="📊 Cohort Analysis")

# --- Uploading Logic ---
# Initialize session state
if 'donor_data' not in st.session_state:
    st.session_state['donor_data'] = pd.DataFrame()
if 'uploaded_file_names' not in st.session_state:
    st.session_state['uploaded_file_names'] = []
if 'last_uploaded_files' not in st.session_state:
    st.session_state['last_uploaded_files'] = []

# Helper function to deduplicate column names
def deduplicate_columns(columns):
    seen = {}
    new_cols = []
    for col in columns:
        if col not in seen:
            seen[col] = 1
            new_cols.append(col)
        else:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
    return new_cols

# File uploader
uploaded_files = st.sidebar.file_uploader(
    "Upload GiveButter Donation Files",
    type=["xlsx"],
    accept_multiple_files=True,
    key="uploader"
)

# Detect and remove files only if uploader widget returns active files
if uploaded_files:
    current_file_names = [f.name for f in uploaded_files]

    # Check for removed files (user clicked grey X)
    removed_files = list(set(st.session_state['last_uploaded_files']) - set(current_file_names))
    if removed_files:
        st.session_state['donor_data'] = st.session_state['donor_data'][
            ~st.session_state['donor_data']['Source File'].isin(removed_files)
        ]
        st.session_state['uploaded_file_names'] = [
            f for f in st.session_state['uploaded_file_names'] if f not in removed_files
        ]

    # Process new files
    new_data = []
    new_file_names = []

    for file in uploaded_files:
        if file.name in st.session_state['uploaded_file_names']:
            continue
        try:
            sheet = pd.ExcelFile(file).sheet_names[0]
            df = pd.read_excel(file, sheet_name=sheet, header=1)
            df.columns = deduplicate_columns(df.columns.str.strip())

            # Normalize expected column names
            df.rename(columns={'Transaction Date (UTC)': 'Date', 'Amount': 'Donation Amount', 'Postal Code': 'ZIP'}, inplace=True)

            # Safe filtering
            first_name_series = df.get('First Name', pd.Series([None]*len(df)))
            org_name_series = df.get('Business/Organization Name', pd.Series([None]*len(df)))
            df = df[first_name_series.notna() | org_name_series.notna()]

            df['Donation Amount'] = pd.to_numeric(df.get('Donation Amount'), errors='coerce')
            df['Date'] = pd.to_datetime(df.get('Date'), errors='coerce')
            org_name_series = df.get('Business/Organization Name', pd.Series([None]*len(df)))
            df['Donor Type'] = org_name_series.apply(lambda x: 'Organization' if pd.notna(x) else 'Individual')
            df['Source File'] = file.name

            new_data.append(df)
            new_file_names.append(file.name)
        except Exception as e:
            st.warning(f"⚠️ Could not process `{file.name}`: {e}")

    if new_data:
        st.session_state['donor_data'] = pd.concat([st.session_state['donor_data']] + new_data, ignore_index=True)
        st.session_state['uploaded_file_names'].extend(new_file_names)

    # Update file state
    st.session_state['last_uploaded_files'] = current_file_names

# Display sidebar info
st.sidebar.markdown("### 📂 Files Processed:")
for name in st.session_state['uploaded_file_names']:
    st.sidebar.markdown(f"• `{name}`")

# Placeholder confirmation
if not st.session_state['donor_data'].empty:
    st.success("✅ Data loaded and persistent across pages.")
else:
    st.info("📥 Please upload donation file(s) to begin.")

# ------------------------- DATA ANALYSIS AND DISPLAY ---------------------------------
if 'donor_data' in st.session_state and not st.session_state['donor_data'].empty:
    df = st.session_state['donor_data']
    # --- Fundraising Trend ---
    st.subheader("📅 Fundraising Over Time")
    time_df = df.copy()
    time_df = time_df.dropna(subset=['Date'])
    time_df['Month'] = time_df['Date'].dt.to_period('M').dt.to_timestamp()
    monthly_donations = time_df.groupby('Month')['Donation Amount'].sum().reset_index()
    monthly_donations['Cumulative Total'] = monthly_donations['Donation Amount'].cumsum()

    brush = alt.selection_interval(encodings=['x'])

    base = alt.Chart(monthly_donations).encode(
        x=alt.X('Month:T', title='Month'),
        y=alt.Y('Cumulative Total:Q', title='Cumulative Donations'),
        tooltip=['Month', 'Cumulative Total']
    )

    area = base.mark_area(opacity=0.3, color="#FDBA21").add_selection(brush)
    line = base.mark_line(color='#F25C54', point=False)

    # Define text for relative gain in highlighted region
    start_value = alt.Chart(monthly_donations).transform_filter(brush).mark_rule(color='gray').encode(
        x='min(Month):T'
    )
    end_value = alt.Chart(monthly_donations).transform_filter(brush).mark_rule(color='gray').encode(
        x='max(Month):T'
    )

    summary_text = alt.Chart(monthly_donations).transform_filter(brush).transform_aggregate(
        start_value='min(Cumulative Total)',
        end_value='max(Cumulative Total)',
        start_month='min(Month)',
        end_month='max(Month)'
    ).transform_calculate(
        percent_increase='(datum.end_value - datum.start_value) / datum.start_value * 100',
        formatted_text='"From " + timeFormat(datum.start_month, "%b %Y") + " to " + timeFormat(datum.end_month, "%b %Y") + ": +" + format(datum.percent_increase, ".1f") + "%"'
    ).mark_text(
        align='left',
        baseline='top',
        dx=15,
        dy=10,
        fontSize=14,
        fontWeight='bold',
        color='#1F3C4C'
    ).encode(
        x=alt.value(10),
        y=alt.value(10),
        text='formatted_text:N'
    )

    time_chart = (area + line + start_value + end_value + summary_text).properties(height=400)

    st.altair_chart(time_chart.configure_view(
        stroke=None,
        fill='#ffffff'
    ).configure_axis(
        labelColor='#1F3C4C',
        titleColor='#1F3C4C'
    ).configure_title(color='#1F3C4C'), use_container_width=True)

    # --- Overview Stats ---
    total_donations = df['Donation Amount'].sum()
    unique_donors = df['Email'].nunique()
    repeat_donors = df['Email'].value_counts().loc[lambda x: x > 1].count()
    org_donors = (df['Donor Type'] == 'Organization').sum()

    st.markdown("""<div class="metric-container">""", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Raised", f"${total_donations:,.0f}")
    col2.metric("Unique Donors", unique_donors)
    col3.metric("Repeat Donors", repeat_donors)
    col4.metric("Organizations", org_donors)

    # --- Campaign Performance and Donor Demographics ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📌 Campaign Performance")
        campaign_summary = df.groupby('Campaign Title')['Donation Amount'].agg(['sum', 'count', 'mean']).reset_index()
        campaign_summary = campaign_summary.rename(columns={
            'sum': 'Total Raised', 'count': 'Donation Count', 'mean': 'Average Gift'
        })
        campaign_summary['Total Raised'] = pd.to_numeric(campaign_summary['Total Raised'], errors='coerce')
        campaign_summary = campaign_summary.dropna(subset=['Total Raised'])

        st.altair_chart(
            alt.Chart(campaign_summary).mark_bar().encode(
                x=alt.X('Campaign Title:N', sort='-y'),
                y=alt.Y('Total Raised:Q'),
                tooltip=['Campaign Title', 'Total Raised']
            ).properties(height=300),
            use_container_width=True
        )

        campaign_n = st.selectbox("Number of campaigns to show in detail:", ['All', 10, 25, 50, 100], index=1)
        with st.expander("See campaign detail table", expanded=False):
            st.dataframe(campaign_summary if campaign_n == 'All' else campaign_summary.head(campaign_n))

    with col2:
        st.subheader("🌍 Donor Demographics")
        if 'ZIP' in df.columns:
            zip_summary = df.groupby('ZIP')['Donation Amount'].sum().sort_values(ascending=False)
            zip_data = zip_summary.head(10).reset_index()
            zip_pie = alt.Chart(zip_data).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Donation Amount", type="quantitative"),
                color=alt.Color(field="ZIP", type="nominal",
                                scale=alt.Scale(range=["#FDBA21", "#F25C54", "#6096BA", "#57B894", "#F49F0A", "#EF476F", "#118AB2", "#06D6A0", "#FFD166", "#8D99AE"])),
                tooltip=["ZIP", "Donation Amount"]
            ).properties(height=300)
            st.altair_chart(zip_pie.configure_view(
                stroke=None,
                fill='#ffffff'
            ).configure_legend(
                labelColor='#1F3C4C',
                titleColor='#1F3C4C'
            ), use_container_width=True)

        zip_n = st.selectbox("Number of ZIP codes to show in detail:", ['All', 10, 25, 50, 100], index=1, key="zip")
        with st.expander("See ZIP code donation detail", expanded=False):
            st.dataframe(zip_summary.reset_index() if zip_n == 'All' else zip_summary.head(zip_n).reset_index())

    # --- Retention Overview ---
    with col1:
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
        st.altair_chart(retention_pie.configure_view(
                stroke=None,
                fill='#ffffff'
            ).configure_legend(
                labelColor='#1F3C4C',
                titleColor='#1F3C4C'
            ), use_container_width=True)

        retention_n = st.selectbox("Number of donors to show in retention detail:", ['All', 10, 25, 50, 100], index=1, key="retention")
        with st.expander("See retention donor detail", expanded=False):
            st.dataframe(donor_dates.reset_index() if retention_n == 'All' else donor_dates.reset_index().head(retention_n))

    # --- Pareto Principle ---
    with col2:
        st.subheader("📈 Pareto Principle (Top Donors)")
        st.markdown("""
        The Pareto Principle (also known as the 80/20 rule) suggests that roughly 80% of outcomes come from 20% of the causes. 
        In fundraising, this often means a small number of donors contribute the majority of donations. 

        This chart helps CVC identify those top donors to prioritize for stewardship, engagement, and retention efforts.
        """)

        # Let user choose target cumulative donation percentage
        target_pct = st.slider("Target Cumulative % of Donations:", min_value=10, max_value=100, value=80, step=5)

        pareto_df = df.groupby('Email')['Donation Amount'].sum().sort_values(ascending=False).reset_index()
        pareto_df['Cumulative %'] = pareto_df['Donation Amount'].cumsum() / pareto_df['Donation Amount'].sum() * 100
        pareto_df['Donor Rank'] = pareto_df.index + 1

        cutoff_index = pareto_df[pareto_df['Cumulative %'] <= target_pct].shape[0] + 1
        display_df = pareto_df.head(cutoff_index)

        bar = alt.Chart(display_df).mark_bar(opacity=0.7).encode(
            x=alt.X('Donor Rank:O', title='Donors (ranked)'),
            y=alt.Y('Donation Amount:Q', title='Donation Amount'),
            tooltip=['Email', 'Donation Amount']
        )

        line = alt.Chart(display_df).mark_line(color='#FDBA21', point=True).encode(
            x='Donor Rank:O',
            y=alt.Y('Cumulative %:Q', axis=alt.Axis(title='Cumulative % of Donations')),
            tooltip=['Email', 'Cumulative %']
        )

        st.altair_chart((bar + line).resolve_scale(y='independent').properties(height=300), use_container_width=True)
        with st.expander("See top donor breakdown table", expanded=False):
            st.dataframe(display_df)


st.markdown("""
<style>
.nav-button-container {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}

.nav-button {
    background-color: #FDBA21;
    color: #1F3C4C;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    border: none;
    font-size: 16px;
    text-decoration: none;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: all 0.3s ease-in-out;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

.nav-button:hover {
    background-color: #f9a602;
    color: white;
    transform: translateY(-2px);
}
</style>
</div>
""", unsafe_allow_html=True)
st.markdown("<hr style='border-top: 3px solid #FDBA21; margin-top: -10px;'>", unsafe_allow_html=True)